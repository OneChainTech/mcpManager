# MCP金融服务管理平台

一个基于FastAPI和MCP协议的金融服务管理平台，支持API服务的注册、管理和调用。该平台通过MCP协议将HTTP API服务暴露为可调用的工具，实现服务的统一管理和代理调用。

## 🚀 核心功能特性

- **🔧 MCP协议集成**: 基于fastapi-mcp实现MCP协议支持，将HTTP API暴露为MCP工具
- **📊 服务管理**: 完整的服务CRUD操作（创建、读取、更新、删除）
- **🌐 API代理**: 通过`/proxy`端点代理调用注册的上游服务
- **🎨 现代化管理界面**: 基于Tailwind CSS的响应式Web管理界面
- **📝 灵活配置**: 支持自定义HTTP方法、请求参数、响应参数等
- **⚡ 实时生效**: 服务配置修改后立即生效，无需重启
- **🔒 参数验证**: 支持JSON格式的参数验证和类型检查

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   MCP Client    │    │   FastAPI App   │    │  Upstream      │
│                 │◄──►│   (Port:8000)   │◄──►│  Services      │
│                 │    │                 │    │  (Port:9001)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                       ┌─────────────────┐
                       │   SQLite DB     │
                       │  mcp_manager.db │
                       └─────────────────┘
```

### 核心组件

- **`main.py`**: 主应用入口，集成FastAPI和MCP协议
- **`mcp_service_manager.py`**: 服务管理器，处理服务的CRUD操作
- **`service_management_api.py`**: 服务管理API路由
- **`test_services.py`**: 模拟上游服务，提供测试接口

## 🚀 快速开始

### 使用启动脚本（推荐）

```bash
# 给脚本添加执行权限
chmod +x start.sh

# 启动所有服务
./start.sh

# 或者手动启动
python main.py
```

### 手动启动

```bash
# 1. 创建虚拟环境
python3 -m venv venv

# 2. 激活虚拟环境
source venv/bin/activate

# 3. 安装依赖
pip install -r requirements.txt

# 4. 启动主服务
python main.py

# 5. 启动测试服务（可选，新终端）
python test_services.py
```

## 🌐 服务端点

### 主服务 (端口: 8000)

| 端点 | 方法 | 描述 |
|------|------|------|
| `/admin` | GET | 服务管理Web界面 |
| `/proxy` | POST | MCP代理调用端点 |
| `/tools` | GET | 获取可用工具列表 |
| `/health` | GET | 健康检查 |
| `/api/services` | GET | 获取服务列表 |
| `/api/services` | POST | 创建新服务 |
| `/api/services/{id}` | PUT | 更新服务 |
| `/api/services/{id}` | DELETE | 删除服务 |

### 测试服务 (端口: 9001)

| 端点 | 方法 | 描述 |
|------|------|------|
| `/products` | GET | 理财产品查询 |
| `/purchase` | POST | 理财产品购买 |

## 📊 数据模型

### UpstreamService 模型

```python
class UpstreamService(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str                    # 服务名称
    summary: str                 # 服务描述
    url: str                     # 服务基础URL
    service_path: str            # 服务路径
    method: str                  # HTTP方法 (GET/POST)
    request_params: dict | None  # 请求参数定义
    response_params: dict | None # 响应参数定义
```

## 🔧 使用示例

### 1. 通过Web界面注册服务

1. 访问 http://127.0.0.1:8000/admin
2. 点击"展开"按钮
3. 填写服务信息：
   - 服务名称: `product-query-service`
   - HTTP方法: `GET`
   - 服务地址: `http://127.0.0.1:9001`
   - 服务路径: `/products`
   - 请求参数: `{"product_type": "string", "risk_level": "string"}`
   - 服务描述: `理财产品查询服务`

### 2. 通过API调用服务

```bash
# 直接调用注册的服务
curl -X POST http://127.0.0.1:8000/proxy \
  -H "Content-Type: application/json" \
  -d '{
    "method": "GET",
    "path": "/products",
    "service_id": 1,
    "params": {"product_type": "fund", "risk_level": "low"}
  }'
```

### 3. 通过MCP协议调用

```python
# 使用MCP客户端调用
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

async with stdio_client(StdioServerParameters()) as (read, write):
    async with ClientSession(read, write) as session:
        # 调用代理工具
        result = await session.call_tool(
            "proxy_call",
            arguments={
                "service_id": 1,
                "path": "/products",
                "params": {"product_type": "fund"}
            }
        )
```

## 🛠️ 开发说明

### 依赖包

- **`fastapi==0.116.1`**: 现代Web框架
- **`uvicorn==0.35.0`**: ASGI服务器
- **`sqlmodel==0.0.24`**: 基于Pydantic的ORM
- **`httpx==0.28.1`**: 异步HTTP客户端
- **`fastapi-mcp==0.4.0`**: MCP协议支持
- **`jinja2==3.1.6`**: 模板引擎

### 数据库

- 使用SQLite数据库 (`mcp_manager.db`)
- 自动创建表结构和迁移
- 支持服务配置持久化

### 配置

- 默认超时时间: 15秒 (可通过环境变量 `UPSTREAM_TIMEOUT` 配置)
- 主服务端口: 8000 (可通过环境变量 `PORT` 配置)
- 测试服务端口: 9001 (可通过环境变量 `TEST_PORT` 配置)

## 🔍 故障排除

### 端口被占用

```bash
# 查看端口占用
lsof -i :8000
lsof -i :9001

# 终止进程
kill -9 <PID>
```

### 服务启动失败

```bash
# 检查依赖安装
pip list | grep fastapi

# 检查Python版本 (需要3.8+)
python --version
```

### 数据库问题

```bash
# 重新初始化数据库
rm mcp_manager.db
python main.py  # 会自动创建新数据库
```

## 📁 项目结构

```
mcpManager/
├── main.py                    # 主应用入口，集成FastAPI和MCP
├── mcp_service_manager.py     # 服务管理器核心逻辑
├── service_management_api.py  # 服务管理API路由
├── test_services.py          # 模拟上游服务
├── templates/
│   └── admin.html           # 管理界面模板
├── start.sh                 # 启动脚本
├── requirements.txt         # Python依赖
├── mcp_manager.db          # SQLite数据库
└── README.md               # 项目说明
```

## 🔄 工作流程

1. **服务注册**: 通过Web界面或API注册上游服务
2. **MCP集成**: 自动将服务暴露为MCP工具
3. **代理调用**: 通过`/proxy`端点代理调用上游服务
4. **结果返回**: 将上游服务响应返回给调用方

## 📈 扩展性

- 支持任意HTTP API服务的注册
- 可配置的请求参数和响应参数
- 灵活的HTTP方法支持
- 可扩展的MCP工具集

## 📄 许可证

MIT License

## 🤝 贡献

欢迎提交Issue和Pull Request来改进这个项目！
