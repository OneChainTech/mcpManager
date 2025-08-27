#!/usr/bin/env python3
"""
服务管理API
提供服务的CRUD操作端点
"""

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, Body, Depends
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi import Request
from sqlmodel import Session

from mcp_service_manager import MCPServiceManager, UpstreamService

# 创建路由器
router = APIRouter(prefix="/api", tags=["服务管理"])

# 模板
templates = Jinja2Templates(directory="templates")

# 服务管理器实例（需要在main.py中初始化）
mcp_service_manager: MCPServiceManager = None

def set_service_manager(manager: MCPServiceManager):
    """设置服务管理器实例"""
    global mcp_service_manager
    mcp_service_manager = manager

def get_db():
    """获取数据库会话"""
    if mcp_service_manager is None:
        raise HTTPException(status_code=500, detail="服务管理器未初始化")
    return mcp_service_manager.get_db()

@router.get("/services", response_model=List[UpstreamService])
def list_services_api(session: Session = Depends(get_db)) -> List[UpstreamService]:
    """获取所有服务列表"""
    return mcp_service_manager.list_services(session)

@router.post("/services", response_model=UpstreamService)
def create_service_api(payload: Dict[str, Any] = Body(...), session: Session = Depends(get_db)) -> UpstreamService:
    """创建新服务"""
    return mcp_service_manager.create_service(payload, session)

@router.get("/services/{service_id}", response_model=UpstreamService)
def get_service_api(service_id: int, session: Session = Depends(get_db)) -> UpstreamService:
    """获取指定服务"""
    return mcp_service_manager.get_service(service_id, session)

@router.put("/services/{service_id}", response_model=UpstreamService)
def update_service_api(service_id: int, payload: Dict[str, Any] = Body(...), session: Session = Depends(get_db)) -> UpstreamService:
    """更新服务"""
    return mcp_service_manager.update_service(service_id, payload, session)

@router.delete("/services/{service_id}")
def delete_service_api(service_id: int, session: Session = Depends(get_db)) -> Dict[str, str]:
    """删除服务"""
    return mcp_service_manager.delete_service(service_id, session)

# 管理页面
@router.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request) -> HTMLResponse:
    """管理页面"""
    return templates.TemplateResponse("admin.html", {"request": request})
