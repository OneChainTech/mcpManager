# MCP金融服务管理平台 API 使用示例

本文档提供了详细的API使用示例，帮助开发者快速上手。

## 🚀 快速开始

### 1. 启动服务

```bash
# 使用启动脚本
./start.sh start

# 或手动启动
python main.py
```

### 2. 访问管理界面

打开浏览器访问：http://127.0.0.1:8000/admin

## 📋 API 端点总览

| 端点 | 方法 | 描述 | 认证 |
|------|------|------|------|
| `/admin` | GET | Web管理界面 | 无 |
| `/health` | GET | 健康检查 | 无 |
| `/tools` | GET | 获取可用工具列表 | 无 |
| `/proxy` | POST | MCP代理调用 | 无 |
| `/api/services` | GET | 获取服务列表 | 无 |
| `/api/services` | POST | 创建新服务 | 无 |
| `/api/services/{id}` | GET | 获取指定服务 | 无 |
| `/api/services/{id}` | PUT | 更新服务 | 无 |
| `/api/services/{id}` | DELETE | 删除服务 | 无 |
| `/api/config` | GET | 获取配置 | 无 |
| `/api/config` | PUT | 更新配置 | 无 |

## 🔧 服务管理 API

### 1. 创建服务

```bash
curl -X POST http://127.0.0.1:8000/api/services \
  -H "Content-Type: application/json" \
  -d '{
    "name": "product-query-service",
    "summary": "理财产品查询服务",
    "url": "http://127.0.0.1:9001",
    "service_path": "/products",
    "method": "GET",
    "request_params": {
      "product_type": "string",
      "risk_level": "string",
      "min_amount": "number",
      "max_amount": "number"
    },
    "response_params": {
      "products": "array",
      "total_count": "number",
      "status": "string"
    }
  }'
```

**响应示例：**
```json
{
  "id": 1,
  "name": "product-query-service",
  "summary": "理财产品查询服务",
  "url": "http://127.0.0.1:9001",
  "service_path": "/products",
  "method": "GET",
  "request_params": {
    "product_type": "string",
    "risk_level": "string",
    "min_amount": "number",
    "max_amount": "number"
  },
  "response_params": {
    "products": "array",
    "total_count": "number",
    "status": "string"
  }
}
```

### 2. 获取服务列表

```bash
curl -X GET http://127.0.0.1:8000/api/services
```

### 3. 获取指定服务

```bash
curl -X GET http://127.0.0.1:8000/api/services/1
```

### 4. 更新服务

```bash
curl -X PUT http://127.0.0.1:8000/api/services/1 \
  -H "Content-Type: application/json" \
  -d '{
    "summary": "更新后的服务描述",
    "request_params": {
      "product_type": "string",
      "risk_level": "string"
    }
  }'
```

### 5. 删除服务

```bash
curl -X DELETE http://127.0.0.1:8000/api/services/1
```

## 🌐 代理调用 API

### 1. 基本调用

```bash
curl -X POST http://127.0.0.1:8000/proxy \
  -H "Content-Type: application/json" \
  -d '{
    "method": "GET",
    "path": "/products",
    "service_id": 1,
    "params": {
      "product_type": "fund",
      "risk_level": "low"
    }
  }'
```

### 2. 带请求体的调用

```bash
curl -X POST http://127.0.0.1:8000/proxy \
  -H "Content-Type: application/json" \
  -d '{
    "method": "POST",
    "path": "/purchase",
    "service_id": 2,
    "json": {
      "product_id": "FUND001",
      "user_id": "USER123",
      "amount": 5000
    }
  }'
```

### 3. 自定义超时

```bash
curl -X POST http://127.0.0.1:8000/proxy \
  -H "Content-Type: application/json" \
  -d '{
    "method": "GET",
    "path": "/products",
    "service_id": 1,
    "timeout": 30
  }'
```

## 🛠️ MCP 协议调用

### 1. 获取可用工具

```bash
curl -X GET http://127.0.0.1:8000/tools
```

**响应示例：**
```json
[
  {
    "id": 1,
    "name": "product-query-service",
    "summary": "理财产品查询服务",
    "url": "http://127.0.0.1:9001",
    "service_path": "/products",
    "method": "GET",
    "request_params": {
      "product_type": "string",
      "risk_level": "string"
    },
    "response_params": {
      "products": "array",
      "total_count": "number"
    }
  }
]
```

### 2. Python MCP 客户端示例

```python
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
import asyncio

async def main():
    async with stdio_client(StdioServerParameters()) as (read, write):
        async with ClientSession(read, write) as session:
            # 列出可用工具
            tools = await session.list_tools()
            print("可用工具:", tools)
            
            # 调用代理工具
            result = await session.call_tool(
                "proxy_call",
                arguments={
                    "service_id": 1,
                    "path": "/products",
                    "params": {"product_type": "fund"}
                }
            )
            print("调用结果:", result)

if __name__ == "__main__":
    asyncio.run(main())
```

## 📊 配置管理 API

### 1. 获取配置

```bash
curl -X GET http://127.0.0.1:8000/api/config
```

**响应示例：**
```json
{
  "id": 1,
  "default_timeout_seconds": 15.0
}
```

### 2. 更新配置

```bash
curl -X PUT http://127.0.0.1:8000/api/config \
  -H "Content-Type: application/json" \
  -d '{
    "default_timeout_seconds": 30.0
  }'
```

## 🔍 健康检查

```bash
curl -X GET http://127.0.0.1:8000/health
```

**响应示例：**
```json
{
  "status": "ok"
}
```

## 📝 错误处理

### 常见错误码

| 状态码 | 描述 | 解决方案 |
|--------|------|----------|
| 400 | 请求参数错误 | 检查请求体格式和必需参数 |
| 404 | 服务不存在 | 确认service_id是否正确 |
| 502 | 上游服务错误 | 检查上游服务是否正常运行 |
| 500 | 内部服务器错误 | 查看服务日志 |

### 错误响应示例

```json
{
  "detail": "服务不存在"
}
```

## 🚀 高级用法

### 1. 批量操作

```bash
# 批量创建服务
for service in service1 service2 service3; do
  curl -X POST http://127.0.0.1:8000/api/services \
    -H "Content-Type: application/json" \
    -d "{\"name\": \"$service\", ...}"
done
```

### 2. 服务监控

```bash
# 监控服务状态
watch -n 5 'curl -s http://127.0.0.1:8000/health'
```

### 3. 日志查看

```bash
# 查看主服务日志
tail -f logs/main.log

# 查看测试服务日志
tail -f logs/test.log
```

## 🔐 安全注意事项

1. **生产环境部署**：建议添加身份验证和授权
2. **HTTPS**：生产环境使用HTTPS加密传输
3. **参数验证**：始终验证输入参数
4. **超时设置**：合理设置超时时间避免资源耗尽
5. **日志管理**：定期清理日志文件

## 📚 更多资源

- [FastAPI 官方文档](https://fastapi.tiangolo.com/)
- [MCP 协议规范](https://modelcontextprotocol.io/)
- [SQLModel 文档](https://sqlmodel.tiangolo.com/)
- [项目 README](../README.md)
