# Headers 字段问题修复说明

## 🚨 问题描述

在检查数据库和管理页面相关逻辑时，发现了一个重要问题：

**问题**: 管理页面的服务注册表单包含 `headers` 字段，但是：
1. 数据库表 `upstreamservice` 中没有 `headers` 字段
2. 数据模型 `UpstreamService` 中缺少 `headers` 属性
3. 服务管理API无法正确处理 `headers` 字段
4. 导致服务注册时 `headers` 信息丢失

## 🔍 问题分析

### 1. 数据库表结构缺失
```sql
-- 原始表结构（缺少headers字段）
CREATE TABLE upstreamservice (
    name VARCHAR NOT NULL,
    summary VARCHAR NOT NULL,
    url VARCHAR NOT NULL,
    service_path VARCHAR NOT NULL,
    method VARCHAR NOT NULL,
    request_params JSON,
    response_params JSON,
    id INTEGER NOT NULL,
    http_method TEXT DEFAULT 'GET',
    default_params JSON
);
```

### 2. 数据模型不完整
```python
# 原始数据模型（缺少headers字段）
class UpstreamServiceBase(SQLModel):
    name: str
    summary: str
    url: str
    service_path: str = Field(default="")
    method: str = Field(default="GET")
    request_params: dict | None = Field(default=None, sa_column=Column(SAJSON))
    response_params: dict | None = Field(default=None, sa_column=Column(SAJSON))
    # 缺少 headers 字段
```

### 3. API处理不完整
- 创建服务时无法保存 `headers` 信息
- 更新服务时无法修改 `headers` 信息
- 服务列表API无法返回 `headers` 信息

## 🛠️ 修复方案

### 1. 更新数据模型
在 `mcp_service_manager.py` 中添加 `headers` 字段：

```python
class UpstreamServiceBase(SQLModel):
    """上游服务基础模型"""
    name: str
    summary: str
    url: str
    service_path: str = Field(default="")
    method: str = Field(default="GET")
    request_params: dict | None = Field(default=None, sa_column=Column(SAJSON))
    response_params: dict | None = Field(default=None, sa_column=Column(SAJSON))
    headers: dict | None = Field(default=None, sa_column=Column(SAJSON))  # 新增

class UpstreamServiceCreateIn(BaseModel):
    """创建服务输入模型"""
    name: str
    summary: str
    url: str
    service_path: Optional[str] = ""
    method: Optional[str] = "GET"
    request_params: Optional[Union[str, Dict[str, Any]]] = None
    response_params: Optional[Union[str, Dict[str, Any]]] = None
    headers: Optional[Union[str, Dict[str, Any]]] = None  # 新增

class UpstreamServiceUpdateIn(BaseModel):
    """更新服务输入模型"""
    name: Optional[str] = None
    summary: Optional[str] = None
    url: Optional[str] = None
    service_path: Optional[str] = None
    method: Optional[str] = None
    request_params: Optional[Union[str, Dict[str, Any]]] = None
    response_params: Optional[Union[str, Dict[str, Any]]] = None
    headers: Optional[Union[str, Dict[str, Any]]] = None  # 新增
```

### 2. 更新服务管理器
在 `MCPServiceManager` 类中添加 `headers` 字段处理：

```python
def create_service(self, payload: Dict[str, Any], session: Session) -> UpstreamService:
    # ... 其他字段处理 ...
    headers = _parse_json_params(payload.get("headers"))  # 新增
    
    svc = UpstreamService(
        name=name,
        summary=summary,
        url=url,
        service_path=service_path,
        method=method,
        request_params=request_params,
        response_params=response_params,
        headers=headers,  # 新增
    )
    # ... 保存逻辑 ...

def update_service(self, service_id: int, payload: Dict[str, Any], session: Session) -> UpstreamService:
    # ... 其他字段更新 ...
    if "headers" in payload:
        svc.headers = _parse_json_params(payload.get("headers"))  # 新增
    # ... 保存逻辑 ...

def get_tools(self, session: Session) -> List[Dict[str, Any]]:
    # ... 服务列表处理 ...
    for service in services:
        tool = {
            # ... 其他字段 ...
            "headers": service.headers or {}  # 新增
        }
        tools.append(tool)
```

### 3. 数据库迁移
创建并运行迁移脚本 `migrate_add_headers.py`：

```python
def migrate_add_headers():
    """添加headers字段到upstreamservice表"""
    # 检查字段是否存在
    cursor.execute("PRAGMA table_info(upstreamservice)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'headers' not in columns:
        # 添加headers字段
        cursor.execute("ALTER TABLE upstreamservice ADD COLUMN headers JSON")
        # 为现有记录设置默认值
        cursor.execute("UPDATE upstreamservice SET headers = '{}' WHERE headers IS NULL")
```

## ✅ 修复结果

### 1. 数据库表结构
```sql
-- 修复后的表结构
CREATE TABLE upstreamservice (
    name VARCHAR NOT NULL,
    summary VARCHAR NOT NULL,
    url VARCHAR NOT NULL,
    service_path VARCHAR NOT NULL,
    method VARCHAR NOT NULL,
    request_params JSON,
    response_params JSON,
    id INTEGER NOT NULL,
    http_method TEXT DEFAULT 'GET',
    default_params JSON,
    headers JSON  -- 新增字段
);
```

### 2. API响应
```json
{
    "id": 1,
    "name": "ranking-service",
    "summary": "理财产品筛选查询",
    "url": "http://127.0.0.1:9001",
    "service_path": "/products",
    "method": "GET",
    "request_params": {...},
    "response_params": {...},
    "headers": {}  // 现在正确返回
}
```

### 3. 功能完整性
- ✅ 服务创建时 `headers` 字段正确保存
- ✅ 服务更新时 `headers` 字段正确修改
- ✅ 服务列表API正确返回 `headers` 信息
- ✅ 管理页面表单 `headers` 字段正常工作

## 🧪 测试验证

### 测试步骤
1. 运行数据库迁移脚本
2. 重启服务
3. 检查服务列表API
4. 验证 `headers` 字段正确返回

### 测试结果
```bash
# 迁移脚本输出
🚀 开始数据库迁移...
正在添加headers字段...
✅ headers字段添加成功

# API测试
curl -s http://127.0.0.1:8000/tools
# 正确返回包含headers字段的JSON数据
```

## 🔮 后续改进

### 1. 数据验证
- 添加 `headers` 字段的格式验证
- 支持自定义请求头的模板配置

### 2. 功能增强
- 支持批量设置请求头
- 添加常用请求头的快速选择

### 3. 监控和日志
- 记录请求头的使用情况
- 监控请求头的有效性

## 📚 相关文档

- [数据模型设计](mcp_service_manager.py)
- [服务管理API](service_management_api.py)
- [管理页面模板](templates/admin.html)
- [数据库迁移脚本](migrate_add_headers.py)
- [代理调用设计](PROXY_CALL_DESIGN.md)
