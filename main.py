from typing import Optional, Dict, Any, List, Iterator

import os
import httpx
from fastapi import FastAPI, HTTPException, Body, Depends
from fastapi.responses import JSONResponse


from sqlmodel import SQLModel, Field, Session, create_engine, select


from fastapi_mcp import FastApiMCP

# 导入MCP服务管理器和服务管理API
from mcp_service_manager import MCPServiceManager
from service_management_api import router as service_router, admin_router, set_service_manager


def log_info(message: str):
    """简单的日志记录"""
    print(f"[INFO] {message}")


# 基础 FastAPI 应用
app = FastAPI(title="API → MCP Proxy")

# =============================
# 数据库与模型
# =============================
DB_URL = "sqlite:///./mcp_manager.db"
engine = create_engine(DB_URL, connect_args={"check_same_thread": False})


class AppConfig(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    default_timeout_seconds: float = Field(default=15.0)


def init_db() -> None:
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        # 确保存在一条配置
        if session.exec(select(AppConfig)).first() is None:
            session.add(AppConfig())
            session.commit()


def get_db() -> Iterator[Session]:
    with Session(engine) as session:
        yield session


@app.on_event("startup")
def on_startup() -> None:
    # 初始化数据库与默认配置
    init_db()

# 读取默认超时从环境变量
DEFAULT_TIMEOUT_SECONDS = float(os.getenv("UPSTREAM_TIMEOUT", "15"))


@app.get("/health", operation_id="health")
async def health() -> Dict[str, str]:
    return {"status": "ok"}


@app.post(
    "/proxy",
    operation_id="proxy_call",
    summary="调用注册的 HTTP 服务接口并返回结果",
)
async def proxy_call(
    request_data: Dict[str, Any] = Body(..., description="请求参数，支持多种格式"),
) -> JSONResponse:
    """
    通用的HTTP服务代理调用函数
    
    支持多种调用格式：
    1. 直接传递参数：{"method": "GET", "path": "/products", "service_id": 1, "params": {}}
    2. MCP格式：{"service_id": 1, "method": "POST", "path": "/purchase", "json": {...}}
    3. 嵌套格式：{"service_id": 1, "data": {"method": "GET", "path": "/products"}}
    4. 通过服务名称：{"service_name": "product-purchase", "method": "POST", "path": "/purchase", "json": {...}}
    5. 智能查找：{"method": "POST", "path": "/purchase", "json": {...}} (自动查找匹配的服务)
    """
    
    # 提取参数，支持多种格式
    method = request_data.get("method")
    path = request_data.get("path")
    service_id = request_data.get("service_id")
    service_name = request_data.get("service_name")
    params = request_data.get("params")
    json_data = request_data.get("json")
    timeout = request_data.get("timeout")
    headers = request_data.get("headers")
    

    
    # 处理MCP客户端的各种调用格式
    # 1. 直接格式：{"method": "GET", "path": "/products", "service_id": 1, "params": {}}
    # 2. MCP格式：{"service_id": 1, "method": "POST", "path": "/purchase", "json": {...}}
    # 3. 嵌套格式：{"service_id": 1, "data": {"method": "GET", "path": "/products"}}
    # 4. 兼容格式：{"service_id": 1, "method": "GET", "path": "/products", "params": {}}
    
    # 处理嵌套格式
    if "data" in request_data:
        data = request_data["data"]
        if isinstance(data, dict):
            method = method or data.get("method")
            path = path or data.get("path")
            params = params or data.get("params")
            json_data = json_data or data.get("json")
            timeout = timeout or data.get("timeout")
            headers = headers or data.get("headers")
    
    # 兼容MCP客户端的参数格式
    # 如果params字段包含完整的请求参数，尝试从中提取
    if isinstance(params, dict) and "method" in params:
        mcp_params = params
        method = method or mcp_params.get("method")
        path = path or mcp_params.get("path")
        json_data = json_data or mcp_params.get("json")
        timeout = timeout or mcp_params.get("timeout")
        headers = headers or mcp_params.get("headers")
        # 重新设置params为实际的查询参数
        params = mcp_params.get("params", {})
    
    # 处理字符串格式的JSON参数
    if isinstance(params, str):
        try:
            import json as json_lib
            params = json_lib.loads(params)
        except:
            pass  # 如果解析失败，保持原值
    
    if isinstance(json_data, str):
        try:
            import json as json_lib
            json_data = json_lib.loads(json_data)
        except:
            pass  # 如果解析失败，保持原值
    
    # 验证必需参数
    if not service_id and not service_name:
        # 智能服务查找：尝试通过path和method自动匹配服务
        if path and method:
            with Session(engine) as session:
                # 查找所有服务
                all_services = mcp_service_manager.list_services(session)
                matched_service = None
                
                # 优先匹配：完全匹配path和method
                for svc in all_services:
                    if svc.service_path == path and svc.method.upper() == method.upper():
                        matched_service = svc
                        break
                
                # 次优先匹配：匹配path（忽略method）
                if not matched_service:
                    for svc in all_services:
                        if svc.service_path == path:
                            matched_service = svc
                            break
                
                # 模糊匹配：path包含关系
                if not matched_service:
                    for svc in all_services:
                        if path in svc.service_path or svc.service_path in path:
                            matched_service = svc
                            break
                
                if matched_service:
                    service_id = matched_service.id
                    service_name = matched_service.name
                    log_info(f"智能匹配到服务: {matched_service.name} (ID: {matched_service.id})")
                else:
                    # 提供更友好的错误信息，包含可用的服务列表
                    available_services = [f"{svc.name} ({svc.method} {svc.service_path})" for svc in all_services]
                    error_msg = f"无法自动匹配服务。当前请求: {method} {path}\n"
                    error_msg += f"可用的服务: {', '.join(available_services)}"
                    raise HTTPException(status_code=400, detail=error_msg)
        else:
            raise HTTPException(status_code=400, detail="缺少必需参数: service_id 或 service_name，且无法自动匹配服务")
    
    # 通过服务名称查找服务ID
    if not service_id and service_name:
        with Session(engine) as session:
            svc = mcp_service_manager.get_service_by_name(service_name, session)
            if svc:
                service_id = svc.id
            else:
                raise HTTPException(status_code=404, detail=f"服务不存在 (名称: {service_name})")
    
    # 确保service_id是整数类型
    try:
        service_id = int(service_id)
    except (ValueError, TypeError):
        raise HTTPException(status_code=400, detail="service_id必须是有效的整数")
    
    # 获取服务配置
    with Session(engine) as session:
        svc = mcp_service_manager.get_service(service_id, session)
        if not svc:
            raise HTTPException(status_code=404, detail=f"服务不存在 (ID: {service_id})")
        
        # 如果未显式传入 method/params，则应用服务默认
        if not method:
            method = svc.method or "GET"
        method_upper = method.upper()
        if not params and svc.request_params:
            params = dict(svc.request_params)
        
        # 构建完整的基础URL：服务地址
        base_url = svc.url
        # 去掉服务地址末尾的斜杠
        if base_url.endswith('/'):
            base_url = base_url[:-1]
        
        client = httpx.AsyncClient(base_url=base_url, timeout=DEFAULT_TIMEOUT_SECONDS)
        close_after = True

    try:
        req_timeout = timeout if timeout is not None else DEFAULT_TIMEOUT_SECONDS
        # 使用服务配置中的service_path作为请求路径
        request_path = svc.service_path if svc.service_path else path
        # 默认使用 JSON 请求头，避免客户端未显式设置时类型错误
        if headers is None:
            headers = {"Content-Type": "application/json"}
        elif "Content-Type" not in headers and "content-type" not in {k.lower() for k in headers.keys()}:
            headers["Content-Type"] = "application/json"
        resp = await client.request(
            method_upper,
            request_path,
            headers=headers,
            params=params,
            json=json_data,
            timeout=req_timeout,
        )
        
        # 记录服务调用统计
        try:
            import httpx as stats_client
            await stats_client.AsyncClient().post(
                "http://127.0.0.1:8000/api/monitoring/record_call",
                json={"service_name": svc.name},
                timeout=1.0
            )
        except:
            pass  # 忽略统计记录错误，不影响主流程
        
        # 返回响应
        content_type = resp.headers.get("content-type", "").lower()
        if "application/json" in content_type:
            try:
                return JSONResponse(status_code=resp.status_code, content=resp.json())
            except:
                return JSONResponse(status_code=resp.status_code, content={"raw": resp.text})
        else:
            return JSONResponse(status_code=resp.status_code, content={"raw": resp.text, "content_type": content_type})
            
    except httpx.HTTPError as e:
        raise HTTPException(status_code=502, detail=f"上游请求异常: {e}")
    finally:
        if close_after:
            try:
                await client.aclose()
            except Exception:
                pass


# =============================
# 配置 API
# =============================
class ConfigIn(SQLModel):
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
    if data.default_timeout_seconds is not None:
        cfg.default_timeout_seconds = float(data.default_timeout_seconds)
    session.add(cfg)
    session.commit()
    session.refresh(cfg)

    # 同步更新运行时的超时配置
    global DEFAULT_TIMEOUT_SECONDS
    DEFAULT_TIMEOUT_SECONDS = cfg.default_timeout_seconds

    return cfg


# 创建MCP服务管理器实例
mcp_service_manager = MCPServiceManager(engine)

# 设置服务管理器实例
set_service_manager(mcp_service_manager)

# 包含服务管理API路由
app.include_router(service_router)
app.include_router(admin_router)


# =============================
# MCP相关端点
# =============================


@app.get(
    "/tools",
    operation_id="tools",
    summary="查询用户已注册的API服务列表",
)
def get_tools(session: Session = Depends(get_db)) -> List[Dict[str, Any]]:
    """获取所有可用的工具（服务）列表"""
    return mcp_service_manager.get_tools(session)

# 使用 fastapi-mcp 将上述 FastAPI 端点暴露为 MCP 工具（优先使用支持 Streamable HTTP 的挂载方式）
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
