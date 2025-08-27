from typing import Optional, Dict, Any, List, Iterator, Union

import os
import httpx
from fastapi import FastAPI, HTTPException, Body, Depends
from fastapi.responses import JSONResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from fastapi.routing import APIRoute
from sqlmodel import SQLModel, Field, Session, create_engine, select
from sqlalchemy import Column, JSON as SAJSON
import json as pyjson
from pydantic import BaseModel
from fastapi_mcp import FastApiMCP

# 导入MCP服务管理器和服务管理API
from mcp_service_manager import MCPServiceManager, UpstreamService
from service_management_api import router as service_router, set_service_manager


# 基础 FastAPI 应用
app = FastAPI(title="API → MCP Proxy")
templates = Jinja2Templates(directory="templates")

# =============================
# 数据库与模型
# =============================
DB_URL = "sqlite:///./mcp_manager.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})


class AppConfig(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    upstream_base_url: str = Field(default="https://httpbin.org")
    default_timeout_seconds: float = Field(default=15.0)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # 确保存在一条配置
        if session.exec(select(AppConfig)).first() is None:
            session.add(AppConfig())
            session.commit()


def migrate_upstream_table() -> None:
    # 轻量迁移：为已有表补充新增列（http_method、default_params）
    try:
        with engine.connect() as conn:
            rows = conn.exec_driver_sql("PRAGMA table_info('upstreamservice')").fetchall()
            columns = {row[1] for row in rows}
            if "http_method" not in columns:
                conn.exec_driver_sql("ALTER TABLE upstreamservice ADD COLUMN http_method TEXT DEFAULT 'GET'")
            if "default_params" not in columns:
                # SQLite 无严格 JSON 类型，这里作为 TEXT 兼容存储 JSON 字符串
                conn.exec_driver_sql("ALTER TABLE upstreamservice ADD COLUMN default_params JSON")
    except Exception:
        # 迁移失败时忽略（开发模式），避免阻断启动
        pass


def get_db() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


@app.on_event("startup")
def on_startup() -> None:
    # 初始化数据库与默认配置
    init_db()
    migrate_upstream_table()


def _normalize_base_url(url: str) -> str:
    if not url:
        return url
    u = url.strip()
    # 去掉尾部斜杠，统一小写协议和主机部分影响较小，这里仅统一整体小写以简单处理
    if u.endswith('/'):
        u = u[:-1]
    return u


# 读取上游 API 基础地址与默认超时从环境变量（可运行时覆盖）
UPSTREAM_BASE_URL = os.getenv("UPSTREAM_BASE_URL", "https://httpbin.org")
DEFAULT_TIMEOUT_SECONDS = float(os.getenv("UPSTREAM_TIMEOUT", "15"))


# 复用一个 httpx.AsyncClient，尽量避免每次请求新建连接
async_client: httpx.AsyncClient | None = None


async def get_async_client() -> httpx.AsyncClient:
    global async_client
    if async_client is None or async_client.is_closed:
        async_client = httpx.AsyncClient(base_url=UPSTREAM_BASE_URL, timeout=DEFAULT_TIMEOUT_SECONDS)
    return async_client


@app.get("/health", operation_id="health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/proxy",
    operation_id="proxy_call",
    summary="转发任意上游 HTTP 接口并返回结果",
)
async def proxy_call(
    method: Optional[str] = Body(default=None, embed=True, description="HTTP 方法，如 GET/POST/PUT/DELETE；若使用 service_id 可不填以采用默认"),
    path: str = Body(..., embed=True, description="相对路径，如 /get 或 /anything"),
    headers: Optional[Dict[str, str]] = Body(default=None, embed=True, description="可选请求头"),
    params: Optional[Dict[str, Any]] = Body(default=None, embed=True, description="查询参数"),
    json: Optional[Any] = Body(default=None, embed=True, description="JSON 请求体"),
    timeout: Optional[float] = Body(default=None, embed=True, description="超时(秒)，不填走默认"),
    service_id: Optional[int] = Body(default=None, embed=True, description="必需：选择注册的上游服务ID"),
) -> JSONResponse:
    method_upper = (method or "").upper()
    allowed_methods = {"GET", "POST", "PUT", "PATCH", "DELETE", "HEAD", "OPTIONS"}
    if method_upper and method_upper not in allowed_methods:
        raise HTTPException(status_code=400, detail=f"不支持的方法: {method}")

    # 必须指定 service_id 来调用用户注册的服务
    if service_id is None:
        raise HTTPException(status_code=400, detail="必须指定 service_id 来调用注册的服务")
    
    with Session(engine) as session:
        svc = mcp_service_manager.get_service(service_id, session)
        # 如果未显式传入 method/params，则应用服务默认
        if not method:
            method_upper = (svc.method or "GET").upper()
        if not params and svc.request_params:
            params = dict(svc.request_params)

        client = httpx.AsyncClient(base_url=svc.url, timeout=DEFAULT_TIMEOUT_SECONDS)
        close_after = True

    try:
        req_timeout = timeout if timeout is not None else DEFAULT_TIMEOUT_SECONDS
        resp = await client.request(
            method_upper,
            path,
            headers=headers,
            params=params,
            json=json,
            timeout=req_timeout,
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"上游请求异常: {e}")
    finally:
        if close_after:
            try:
                await client.aclose()
            except Exception:
                pass

    # 尽量返回上游的 JSON；若不是 JSON，则作为文本返回
    content_type = resp.headers.get("content-type", "").lower()
    if "application/json" in content_type:
        try:
            return JSONResponse(status_code=resp.status_code, content=resp.json())
        except Exception:
            return JSONResponse(status_code=resp.status_code, content={"raw": resp.text})
    else:
        return JSONResponse(status_code=resp.status_code, content={"raw": resp.text, "content_type": content_type})


# =============================
# 配置 API
# =============================
class ConfigIn(SQLModel):
    upstream_base_url: Optional[str] = None
    default_timeout_seconds: Optional[float] = None


@app.get("/api/config", response_model=AppConfig)
def get_config(session: Session = Depends(get_db)) -> AppConfig:
    cfg = session.exec(select(AppConfig)).first()
    assert cfg is not None
    return cfg


@app.put("/api/config", response_model=AppConfig)
def update_config(data: ConfigIn, session: Session = Depends(get_db)) -> AppConfig:
    cfg = session.exec(select(AppConfig)).first()
    assert cfg is not None
    if data.upstream_base_url is not None:
        cfg.upstream_base_url = data.upstream_base_url
    if data.default_timeout_seconds is not None:
        cfg.default_timeout_seconds = float(data.default_timeout_seconds)
    session.add(cfg)
    session.commit()
    session.refresh(cfg)

    # 同步更新运行时的 httpx client 配置
    global UPSTREAM_BASE_URL, DEFAULT_TIMEOUT_SECONDS, async_client
    UPSTREAM_BASE_URL = cfg.upstream_base_url
    DEFAULT_TIMEOUT_SECONDS = cfg.default_timeout_seconds
    if async_client is not None and not async_client.is_closed:
        try:
            awaitable_close = getattr(async_client, "aclose", None)
            if awaitable_close is not None:
                import anyio
                anyio.run(async_client.aclose)
        except Exception:
            pass
        async_client = None

    return cfg


# 创建MCP服务管理器实例
mcp_service_manager = MCPServiceManager(engine)

# 设置服务管理器实例
set_service_manager(mcp_service_manager)

# 包含服务管理API路由
app.include_router(service_router)


# =============================
# MCP相关端点
# =============================


@app.get(
    "/tools",
    operation_id="tools",
    summary="查询用户已添加的API服务列表",
)
def get_tools(session: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """获取所有可用的工具（服务）列表"""
    return mcp_service_manager.get_tools(session)


# 使用 fastapi-mcp 将上述 FastAPI 端点暴露为 MCP 工具
# 优先使用支持 Streamable HTTP 的挂载方式
mcp = FastApiMCP(
    app,
    name="api-proxy-mcp",
    description="将任意 HTTP API 通过 /proxy 工具暴露为 MCP 服务（Streamable HTTP）",
    describe_all_responses=True,
    describe_full_response_schema=True,
    include_operations=["proxy_call", "health", "tools"],  # 暴露这三个端点
)

# 挂载为 Streamable HTTP（fastapi-mcp 文档推荐）
mcp.mount_http()


# 便于本地直接运行
if __name__ == "__main__":
    import uvicorn

    host = os.getenv("HOST", "127.0.0.1")
    port = int(os.getenv("PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
