from typing import Dict, Any

import os
import asyncio
from fastapi import FastAPI, Body
from pydantic import BaseModel


app = FastAPI(title="Upstream Test Services")


# 请求和响应数据模型
class ProductQueryRequest(BaseModel):
    product_type: str = "all"  # 产品类型：all, fund, insurance, p2p
    risk_level: str = "medium"  # 风险等级：low, medium, high
    min_amount: float = 1000.0  # 最小投资金额
    max_amount: float = 1000000.0  # 最大投资金额


class ProductQueryResponse(BaseModel):
    service_name: str = "product-query"
    products: list
    total_count: int
    query_params: dict
    status: str = "success"


class ProductPurchaseRequest(BaseModel):
    product_id: str
    user_id: str
    amount: float
    payment_method: str = "bank_transfer"  # 支付方式
    risk_agreement: bool = True  # 风险协议确认


class ProductPurchaseResponse(BaseModel):
    service_name: str = "product-purchase"
    order_id: str
    product_id: str
    amount: float
    status: str = "processing"
    message: str = "订单已提交，正在处理中"


@app.get("/products")
async def query_products(
    product_type: str = "all",
    risk_level: str = "medium",
    min_amount: float = 1000.0,
    max_amount: float = 1000000.0
) -> ProductQueryResponse:
    # 模拟理财产品数据
    mock_products = [
        {
            "id": "FUND001",
            "name": "稳健增长基金",
            "type": "fund",
            "risk_level": "low",
            "min_amount": 1000,
            "expected_return": "4.5%",
            "duration": "12个月"
        },
        {
            "id": "INS001",
            "name": "年金保险计划",
            "type": "insurance",
            "risk_level": "low",
            "min_amount": 5000,
            "expected_return": "3.8%",
            "duration": "终身"
        },
        {
            "id": "P2P001",
            "name": "企业借贷项目",
            "type": "p2p",
            "risk_level": "high",
            "min_amount": 10000,
            "expected_return": "12.5%",
            "duration": "6个月"
        },
        {
            "id": "FUND002",
            "name": "成长型股票基金",
            "type": "fund",
            "risk_level": "medium",
            "min_amount": 2000,
            "expected_return": "8.2%",
            "duration": "24个月"
        },
        {
            "id": "INS002",
            "name": "重疾保险",
            "type": "insurance",
            "risk_level": "medium",
            "min_amount": 3000,
            "expected_return": "5.5%",
            "duration": "20年"
        }
    ]
    
    # 简化过滤逻辑，确保能返回数据
    filtered_products = []
    for product in mock_products:
        # 如果指定了产品类型且不匹配，则跳过
        if product_type != "all" and product["type"] != product_type:
            continue
        # 如果指定了风险等级且不匹配，则跳过
        if risk_level != "medium" and product["risk_level"] != risk_level:
            continue
        # 如果金额范围不匹配，则跳过
        if product["min_amount"] < min_amount or product["min_amount"] > max_amount:
            continue
        filtered_products.append(product)
    
    # 如果没有匹配的产品，返回所有产品（用于演示）
    if not filtered_products:
        filtered_products = mock_products
    
    return ProductQueryResponse(
        products=filtered_products,
        total_count=len(filtered_products),
        query_params={
            "product_type": product_type,
            "risk_level": risk_level,
            "min_amount": min_amount,
            "max_amount": max_amount
        }
    )


@app.post("/purchase")
async def purchase_product(request: ProductPurchaseRequest) -> ProductPurchaseResponse:
    # 模拟理财产品购买流程
    import uuid
    import time
    
    # 生成订单ID
    order_id = f"ORDER_{int(time.time())}_{uuid.uuid4().hex[:8].upper()}"
    
    # 暂时去掉条件检查，直接处理
    # 模拟处理延迟
    await asyncio.sleep(0.5)
    
    return ProductPurchaseResponse(
        order_id=order_id,
        product_id=request.product_id,
        amount=request.amount,
        status="processing",
        message="订单已提交，正在处理中"
    )





if __name__ == "__main__":
    import uvicorn

    host = os.getenv("TEST_HOST", "127.0.0.1")
    port = int(os.getenv("TEST_PORT", "9001"))
    
    print("🚀 启动理财产品服务 (JSON格式)")
    print(f"地址: http://{host}:{port}")
    print("端点:")
    print("  GET  /products - 理财产品查询服务")
    print("  POST /purchase - 理财产品购买服务")
    
    uvicorn.run(app, host=host, port=port)


