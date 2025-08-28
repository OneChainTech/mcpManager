# Proxy Call 函数设计说明

## 🎯 设计理念

重新设计的 `proxy_call` 函数遵循以下原则：

1. **简洁性**: 去除复杂的参数提取逻辑，专注于核心功能
2. **通用性**: 支持多种调用方式，适应不同的使用场景
3. **健壮性**: 优雅处理各种异常情况，提供清晰的错误信息
4. **标准化**: 遵循 RESTful API 设计原则

## 🏗️ 架构设计

### 核心功能
- **HTTP 代理**: 将请求转发到注册的上游服务
- **参数解析**: 支持直接参数和 MCP 格式两种调用方式
- **响应处理**: 自动识别响应类型并返回合适的格式

### 支持的方法
- **GET**: 查询操作，参数通过 `params` 传递
- **POST**: 创建/提交操作，数据通过 `json` 传递

## 📝 调用方式

### 1. 直接调用方式
```json
{
  "method": "GET",
  "path": "/products",
  "service_id": 1,
  "params": {
    "product_type": "fund",
    "risk_level": "low"
  }
}
```

### 2. MCP 格式调用
```json
{
  "json": {
    "method": "POST",
    "path": "/purchase",
    "service_id": 2,
    "json": "{\"product_id\": \"FUND001\", \"user_id\": \"USER123\", \"amount\": 10000}"
  }
}
```

## 🔧 参数说明

| 参数 | 类型 | 必需 | 说明 |
|------|------|------|------|
| `method` | string | 否 | HTTP 方法，默认使用服务配置 |
| `path` | string | 否 | 请求路径，默认使用服务配置 |
| `service_id` | integer | 是 | 上游服务ID |
| `params` | object/string | 否 | 查询参数（GET请求） |
| `json` | any/string | 否 | 请求体（POST请求） |
| `timeout` | float | 否 | 超时时间（秒） |
| `headers` | object | 否 | 自定义请求头 |

## 🚀 使用示例

### GET 请求示例
```bash
# 查询产品
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

### POST 请求示例
```bash
# 购买产品
curl -X POST http://127.0.0.1:8000/proxy \
  -H "Content-Type: application/json" \
  -d '{
    "method": "POST",
    "path": "/purchase",
    "service_id": 2,
    "json": {
      "product_id": "FUND001",
      "user_id": "USER123",
      "amount": 10000,
      "payment_method": "bank_transfer",
      "risk_agreement": true
    }
  }'
```

## 🔄 工作流程

1. **参数接收**: 接收客户端请求参数
2. **格式识别**: 自动识别是否为 MCP 格式调用
3. **参数提取**: 从 MCP 格式中提取实际参数
4. **JSON 解析**: 处理字符串格式的 JSON 参数
5. **服务验证**: 验证服务ID 是否存在
6. **请求构建**: 构建完整的 HTTP 请求
7. **请求转发**: 使用 httpx 转发请求到上游服务
8. **响应处理**: 处理上游服务响应并返回

## ✨ 特性优势

### 1. 智能参数处理
- 自动识别 MCP 格式调用
- 支持字符串和对象格式的 JSON
- 优雅处理解析失败的情况

### 2. 灵活的调用方式
- 支持直接参数传递
- 支持 MCP 协议格式
- 向后兼容现有调用方式

### 3. 健壮的错误处理
- 清晰的错误信息
- 优雅的异常处理
- 自动资源清理

### 4. 标准化的响应
- 自动识别响应类型
- 统一的响应格式
- 支持多种内容类型

## 🧪 测试验证

### 已测试场景
- ✅ GET 请求（直接调用）
- ✅ POST 请求（直接调用）
- ✅ GET 请求（MCP 格式）
- ✅ POST 请求（MCP 格式）
- ✅ 字符串 JSON 解析
- ✅ 服务不存在处理
- ✅ 参数验证

### 测试结果
所有测试场景均正常工作，响应时间在预期范围内，错误处理完善。

## 🔮 未来扩展

1. **缓存支持**: 添加响应缓存机制
2. **重试机制**: 支持失败重试
3. **监控指标**: 添加性能监控
4. **限流控制**: 支持请求限流
5. **认证授权**: 增强安全控制

## 📚 相关文档

- [API 使用示例](API_EXAMPLES.md)
- [系统架构说明](ARCHITECTURE.md)
- [项目总结](PROJECT_SUMMARY.md)
- [README 文档](README.md)
