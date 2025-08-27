from typing import Dict, Any

import os
import asyncio
from fastapi import FastAPI, Body
from pydantic import BaseModel


app = FastAPI(title="Upstream Test Services")


# 请求和响应数据模型
class EchoRequest(BaseModel):
    message: str = "hello"
    timestamp: float = None
    metadata: Dict[str, Any] = {}


class EchoResponse(BaseModel):
    service: str = "echo"
    message: str
    timestamp: float
    received_data: Dict[str, Any]
    status: str = "success"


class DelayRequest(BaseModel):
    seconds: float = 2.0
    description: str = "Delay operation"
    metadata: Dict[str, Any] = {}


class DelayResponse(BaseModel):
    service: str = "delay"
    slept_seconds: float
    actual_delay: float
    description: str
    status: str = "success"


@app.post("/echo")
async def echo(request: EchoRequest) -> EchoResponse:
    import time
    
    current_time = time.time()
    received_data = {
        "message": request.message,
        "timestamp": request.timestamp,
        "metadata": request.metadata
    }
    
    return EchoResponse(
        message=request.message,
        timestamp=current_time,
        received_data=received_data
    )


@app.post("/delay")
async def delay(request: DelayRequest) -> DelayResponse:
    import time
    
    start_time = time.time()
    # 人为延迟，用于测试超时与重试场景
    await asyncio.sleep(max(0.0, request.seconds))
    end_time = time.time()
    
    actual_delay = end_time - start_time
    
    return DelayResponse(
        slept_seconds=request.seconds,
        actual_delay=actual_delay,
        description=request.description
    )


@app.get("/")
async def root() -> Dict[str, Any]:
    """服务信息端点"""
    return {
        "service": "test-services",
        "description": "测试服务集合 - 提供echo和delay API",
        "version": "2.0.0",
        "endpoints": [
            {
                "path": "/echo",
                "method": "POST",
                "description": "回显服务 - 接收JSON数据并返回回显信息"
            },
            {
                "path": "/delay",
                "method": "POST", 
                "description": "延迟服务 - 接收JSON数据并执行延迟操作"
            }
        ],
        "data_format": "JSON"
    }


if __name__ == "__main__":
    import uvicorn

    host = os.getenv("TEST_HOST", "127.0.0.1")
    port = int(os.getenv("TEST_PORT", "9001"))
    
    print("🚀 启动测试服务 (JSON格式)")
    print(f"地址: http://{host}:{port}")
    print("端点:")
    print("  POST /echo - 回显服务 (JSON)")
    print("  POST /delay - 延迟服务 (JSON)")
    print("  GET  / - 服务信息")
    
    uvicorn.run(app, host=host, port=port)


