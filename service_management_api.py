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
import time
import json
import os

from mcp_service_manager import MCPServiceManager, UpstreamService

# 创建路由器
router = APIRouter(prefix="/api", tags=["服务管理"])

# 创建管理页面路由器（无前缀）
admin_router = APIRouter(tags=["管理页面"])

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
    # 使用服务管理器的get_db方法，但正确处理生成器
    for session in mcp_service_manager.get_db():
        yield session

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

# 监控相关API
@router.get("/monitoring/status")
def get_mcp_status() -> Dict[str, Any]:
    """获取MCP服务状态"""
    try:
        # 检查主服务状态
        main_status = "running"
        test_status = "running"
        
        # 检查进程是否存在
        if os.path.exists(".main.pid"):
            with open(".main.pid", "r") as f:
                main_pid = int(f.read().strip())
                try:
                    os.kill(main_pid, 0)  # 检查进程是否存在
                except OSError:
                    main_status = "stopped"
        else:
            main_status = "stopped"
            
        if os.path.exists(".test.pid"):
            with open(".test.pid", "r") as f:
                test_pid = int(f.read().strip())
                try:
                    os.kill(test_pid, 0)  # 检查进程是否存在
                except OSError:
                    test_status = "stopped"
        else:
            test_status = "stopped"
        
        return {
            "mcp_main_service": {
                "status": main_status,
                "port": 8000,
                "url": "http://127.0.0.1:8000"
            },
            "test_service": {
                "status": test_status,
                "port": 9000,
                "url": "http://127.0.0.1:9000"
            },
            "timestamp": int(time.time())
        }
    except Exception as e:
        return {
            "error": str(e),
            "mcp_main_service": {"status": "unknown"},
            "test_service": {"status": "unknown"},
            "timestamp": int(time.time())
        }

@router.get("/monitoring/stats")
def get_service_stats(session: Session = Depends(get_db)) -> Dict[str, Any]:
    """获取服务调用统计"""
    try:
        # 读取调用统计文件
        stats_file = "logs/service_stats.json"
        if os.path.exists(stats_file):
            with open(stats_file, "r", encoding="utf-8") as f:
                stats_data = json.load(f)
        else:
            stats_data = {}
        
        # 获取所有服务
        services = mcp_service_manager.list_services(session)
        service_stats = []
        
        for service in services:
            service_name = service.name
            call_count = stats_data.get(service_name, {}).get("call_count", 0)
            last_called = stats_data.get(service_name, {}).get("last_called", None)
            
            service_stats.append({
                "id": service.id,
                "name": service_name,
                "call_count": call_count,
                "last_called": last_called,
                "status": "active" if call_count > 0 else "idle"
            })
        
        return {
            "services": service_stats,
            "total_calls": sum(s["call_count"] for s in service_stats),
            "timestamp": int(time.time())
        }
    except Exception as e:
        return {
            "error": str(e),
            "services": [],
            "total_calls": 0,
            "timestamp": int(time.time())
        }

@router.post("/monitoring/record_call")
def record_service_call(service_name: str = Body(..., embed=True)) -> Dict[str, str]:
    """记录服务调用"""
    try:
        stats_file = "logs/service_stats.json"
        
        # 读取现有统计
        if os.path.exists(stats_file):
            with open(stats_file, "r", encoding="utf-8") as f:
                stats_data = json.load(f)
        else:
            stats_data = {}
        
        # 更新统计
        if service_name not in stats_data:
            stats_data[service_name] = {"call_count": 0, "last_called": None}
        
        stats_data[service_name]["call_count"] += 1
        stats_data[service_name]["last_called"] = int(time.time())
        
        # 确保logs目录存在
        os.makedirs("logs", exist_ok=True)
        
        # 写入统计文件
        with open(stats_file, "w", encoding="utf-8") as f:
            json.dump(stats_data, f, indent=2, ensure_ascii=False)
        
        return {"status": "success", "message": f"Recorded call for {service_name}"}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# 管理页面
@admin_router.get("/admin", response_class=HTMLResponse)
def admin_page(request: Request) -> HTMLResponse:
    """管理页面"""
    return templates.TemplateResponse("admin.html", {"request": request})
