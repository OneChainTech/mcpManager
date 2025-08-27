#!/usr/bin/env python3
"""
MCP服务管理器
负责管理上游服务的CRUD操作
"""

from typing import Optional, Dict, Any, List, Union
from sqlmodel import SQLModel, Field, Session, select
from sqlalchemy import Column, JSON as SAJSON
from fastapi import HTTPException, Body, Depends
from pydantic import BaseModel
import json as pyjson


class UpstreamServiceBase(SQLModel):
    """上游服务基础模型"""
    name: str
    summary: str
    url: str
    service_path: str = Field(default="")
    method: str = Field(default="GET")
    request_params: dict | None = Field(default=None, sa_column=Column(SAJSON))
    response_params: dict | None = Field(default=None, sa_column=Column(SAJSON))


class UpstreamService(UpstreamServiceBase, table=True):
    """上游服务数据库模型"""
    id: int | None = Field(default=None, primary_key=True)


class UpstreamServiceCreateIn(BaseModel):
    """创建服务输入模型"""
    name: str
    summary: str
    url: str
    service_path: Optional[str] = ""
    method: Optional[str] = "GET"
    request_params: Optional[Union[str, Dict[str, Any]]] = None
    response_params: Optional[Union[str, Dict[str, Any]]] = None


class UpstreamServiceUpdateIn(BaseModel):
    """更新服务输入模型"""
    name: Optional[str] = None
    summary: Optional[str] = None
    url: Optional[str] = None
    service_path: Optional[str] = None
    method: Optional[str] = None
    request_params: Optional[Union[str, Dict[str, Any]]] = None
    response_params: Optional[Union[str, Dict[str, Any]]] = None


def _normalize_base_url(url: str) -> str:
    """标准化基础URL"""
    if not url:
        return url
    u = url.strip()
    if u.endswith('/'):
        u = u[:-1]
    return u


def _parse_json_params(value: Optional[Union[str, Dict[str, Any]]]) -> Optional[Dict[str, Any]]:
    """解析JSON参数"""
    if value is None:
        return None
    if isinstance(value, dict):
        return value
    if isinstance(value, str):
        try:
            parsed = pyjson.loads(value)
            return parsed if isinstance(parsed, dict) else None
        except Exception:
            return None
    return None


class MCPServiceManager:
    """MCP服务管理器"""
    
    def __init__(self, engine):
        self.engine = engine
    
    def get_db(self):
        """获取数据库会话"""
        with Session(self.engine) as session:
            yield session
    
    def list_services(self, session: Session) -> List[UpstreamService]:
        """列出所有服务"""
        return session.exec(select(UpstreamService)).all()
    
    def get_service(self, service_id: int, session: Session) -> UpstreamService:
        """获取指定服务"""
        svc = session.get(UpstreamService, service_id)
        if not svc:
            raise HTTPException(status_code=404, detail="服务不存在")
        return svc
    
    def create_service(self, payload: Dict[str, Any], session: Session) -> UpstreamService:
        """创建新服务"""
        name = payload.get("name", "")
        summary = payload.get("summary", "")
        url = _normalize_base_url(payload.get("url", ""))
        service_path = payload.get("service_path", "").strip()
        method = (payload.get("method") or "GET").upper()
        request_params = _parse_json_params(payload.get("request_params"))
        response_params = _parse_json_params(payload.get("response_params"))

        svc = UpstreamService(
            name=name,
            summary=summary,
            url=url,
            service_path=service_path,
            method=method,
            request_params=request_params,
            response_params=response_params,
        )
        session.add(svc)
        session.commit()
        session.refresh(svc)
        return svc
    
    def update_service(self, service_id: int, payload: Dict[str, Any], session: Session) -> UpstreamService:
        """更新服务"""
        svc = session.get(UpstreamService, service_id)
        if not svc:
            raise HTTPException(status_code=404, detail="服务不存在")
        
        if "name" in payload:
            svc.name = payload.get("name") or svc.name
        if "summary" in payload:
            svc.summary = payload.get("summary") or svc.summary
        if "url" in payload:
            svc.url = _normalize_base_url(payload.get("url") or svc.url)
        if "service_path" in payload:
            svc.service_path = (payload.get("service_path") or "").strip()
        if "method" in payload:
            hm = payload.get("method")
            if hm is not None:
                svc.method = (hm or "GET").upper()
        if "request_params" in payload:
            svc.request_params = _parse_json_params(payload.get("request_params"))
        if "response_params" in payload:
            svc.response_params = _parse_json_params(payload.get("response_params"))
        
        session.add(svc)
        session.commit()
        session.refresh(svc)
        return svc
    
    def delete_service(self, service_id: int, session: Session) -> Dict[str, str]:
        """删除服务"""
        svc = session.get(UpstreamService, service_id)
        if not svc:
            raise HTTPException(status_code=404, detail="服务不存在")
        session.delete(svc)
        session.commit()
        return {"status": "deleted"}
    
    def get_tools(self, session: Session) -> List[Dict[str, Any]]:
        """获取所有可用的工具（服务）列表"""
        services = session.exec(select(UpstreamService)).all()
        tools = []
        
        for service in services:
            tool = {
                "id": service.id,
                "name": service.name,
                "summary": service.summary,
                "url": service.url,
                "service_path": service.service_path,
                "method": service.method,
                "request_params": service.request_params or {},
                "response_params": service.response_params or {}
            }
            tools.append(tool)
        
        return tools
