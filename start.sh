#!/bin/bash

# 检查虚拟环境是否存在
if [ ! -d "venv" ]; then
    echo "创建虚拟环境..."
    python3 -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖（如果需要）
if [ ! -f "venv/lib/python*/site-packages/fastapi" ]; then
    echo "安装依赖..."
    pip install httpx fastapi uvicorn sqlmodel fastapi-mcp jinja2
fi

# 启动服务
echo "启动MCP服务管理器..."
python main.py
