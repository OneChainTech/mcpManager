# MCP客户端使用指南

## 概述

为了解决MCP客户端在调用`proxy_call`时经常忘记传`service_id`的问题，我们提供了多种解决方案：

## 解决方案1：使用新的简化端点 `/mcp_call`

### 推荐用法（最友好）

```bash
# 通过服务名称调用（推荐）
curl -X POST "http://127.0.0.1:8000/mcp_call" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "product-purchase",
    "method": "POST", 
    "path": "/purchase",
    "json": {
      "product_id": "FUND001",
      "user_id": "test_user",
      "amount": 5000
    }
  }'
```

### 智能匹配（无需指定服务）

```bash
# 自动匹配服务（通过path和method）
curl -X POST "http://127.0.0.1:8000/mcp_call" \
  -H "Content-Type: application/json" \
  -d '{
    "method": "GET",
    "path": "/products",
    "params": {
      "product_type": "fund",
      "risk_level": "low"
    }
  }'
```

## 解决方案2：使用原有端点 `/proxy` 并支持service_name

```bash
# 通过服务名称调用
curl -X POST "http://127.0.0.1:8000/proxy" \
  -H "Content-Type: application/json" \
  -d '{
    "service_name": "product-purchase",
    "method": "POST",
    "path": "/purchase",
    "json": {
      "product_id": "FUND001",
      "user_id": "test_user",
      "amount": 5000
    }
  }'
```

## 支持的调用格式

### 1. 通过服务名称（推荐）
```json
{
  "service_name": "product-purchase",
  "method": "POST",
  "path": "/purchase",
  "json": {...}
}
```

### 2. 通过服务ID
```json
{
  "service_id": 1,
  "method": "POST",
  "path": "/purchase",
  "json": {...}
}
```

### 3. 智能匹配（无需指定服务）
```json
{
  "method": "POST",
  "path": "/purchase",
  "json": {...}
}
```

### 4. 完整参数
```json
{
  "service_name": "product-purchase",
  "method": "POST",
  "path": "/purchase",
  "params": {...},
  "json": {...},
  "headers": {...},
  "timeout": 30
}
```

## 智能匹配规则

当没有明确指定`service_id`或`service_name`时，系统会按以下优先级自动匹配服务：

1. **完全匹配**：path和method都匹配
2. **路径匹配**：只匹配path（忽略method）
3. **模糊匹配**：path包含关系

## 错误处理

### 常见错误及解决方案

1. **缺少必需参数**
   ```
   错误：缺少必需参数: service_id 或 service_name
   解决：添加service_name或service_id，或使用智能匹配
   ```

2. **服务不存在**
   ```
   错误：服务不存在 (名称: product-purchase)
   解决：检查服务名称是否正确，或使用管理界面查看可用服务
   ```

3. **无法自动匹配**
   ```
   错误：无法自动匹配服务，请明确指定 service_id 或 service_name
   解决：明确指定服务标识符，或检查path和method是否正确
   ```

## 最佳实践

1. **优先使用service_name**：比数字ID更直观易记
2. **使用智能匹配**：对于简单调用，让系统自动匹配服务
3. **保持一致性**：在同一个项目中统一使用相同的调用格式
4. **错误处理**：在客户端代码中添加适当的错误处理逻辑

## 示例代码

### Python示例
```python
import requests

def call_mcp_service(service_name, method, path, data=None, params=None):
    url = "http://127.0.0.1:8000/mcp_call"
    payload = {
        "service_name": service_name,
        "method": method,
        "path": path
    }
    
    if data:
        payload["json"] = data
    if params:
        payload["params"] = params
    
    response = requests.post(url, json=payload)
    return response.json()

# 使用示例
result = call_mcp_service(
    service_name="product-purchase",
    method="POST",
    path="/purchase",
    data={"product_id": "FUND001", "user_id": "user123", "amount": 5000}
)
```

### JavaScript示例
```javascript
async function callMCPService(serviceName, method, path, data = null, params = null) {
    const url = "http://127.0.0.1:8000/mcp_call";
    const payload = {
        service_name: serviceName,
        method: method,
        path: path
    };
    
    if (data) payload.json = data;
    if (params) payload.params = params;
    
    const response = await fetch(url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
    });
    
    return await response.json();
}

// 使用示例
const result = await callMCPService(
    "product-purchase",
    "POST",
    "/purchase",
    { product_id: "FUND001", user_id: "user123", amount: 5000 }
);
```

## 总结

通过这些改进，MCP客户端现在可以：

1. ✅ 使用`service_name`代替`service_id`
2. ✅ 使用新的简化端点`/mcp_call`
3. ✅ 享受智能服务匹配功能
4. ✅ 获得更好的错误提示
5. ✅ 保持向后兼容性

选择最适合你需求的方案，让MCP调用变得更加简单和可靠！
