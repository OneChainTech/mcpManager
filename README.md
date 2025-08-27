# MCP 服务管理器

一个用于管理 MCP (Model Context Protocol) 服务的 Web 界面和 API 代理。

## 功能特性

- 🚀 **服务管理**: 添加、编辑、删除上游服务
- ⚙️ **配置管理**: 管理上游基础地址和超时设置
- 🔄 **API 代理**: 转发请求到上游服务
- 📊 **Web 界面**: 直观的管理界面
- 🎯 **MCP 集成**: 支持 MCP 协议

## 服务配置结构

每个服务包含以下字段：

- **name**: 服务名称
- **summary**: 服务描述
- **url**: 服务地址
- **method**: HTTP 方法 (GET/POST)
- **request_params**: 请求参数 (JSON 格式)
- **response_params**: 响应参数 (JSON 格式)

## 快速开始

### 1. 启动服务

```bash
# 使用启动脚本（推荐）
./start.sh

# 或手动启动
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python main.py
```

### 2. 访问管理界面

打开浏览器访问: http://127.0.0.1:8000/admin

### 3. API 端点

- `GET /health` - 健康检查
- `GET /api/services` - 获取所有服务
- `POST /api/services` - 创建新服务
- `PUT /api/services/{id}` - 更新服务
- `DELETE /api/services/{id}` - 删除服务
- `POST /proxy` - 代理请求到上游服务

## 环境变量

- **HOST**: 服务监听地址 (默认: 127.0.0.1)
- **PORT**: 服务监听端口 (默认: 8000)
- **UPSTREAM_BASE_URL**: 上游 API 基础地址 (默认: https://httpbin.org)
- **UPSTREAM_TIMEOUT**: 默认超时时间 (默认: 15秒)

## 使用示例

### 添加服务

```bash
curl -X POST http://127.0.0.1:8000/api/services \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-service",
    "summary": "我的服务",
    "url": "http://127.0.0.1:9001",
    "method": "POST",
    "request_params": {"key": "value"},
    "response_params": {"status": "ok"}
  }'
```

### 代理请求

```bash
curl -X POST http://127.0.0.1:8000/proxy \
  -H "Content-Type: application/json" \
  -d '{
    "method": "GET",
    "path": "/get",
    "service_id": 1
  }'
```

## 技术栈

- **后端**: FastAPI + SQLModel + SQLite
- **前端**: HTML + JavaScript + Jinja2
- **MCP**: fastapi-mcp
- **HTTP 客户端**: httpx

## 许可证

MIT License
