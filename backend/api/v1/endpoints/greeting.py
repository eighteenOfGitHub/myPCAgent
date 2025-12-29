"""
backend/api/v1/endpoints/greeting.py

问候相关的 API 端点。

此模块定义与问候相关的 FastAPI 路由，并调用核心服务层的函数。
"""
from fastapi import APIRouter, HTTPException
from backend.core.services.greeting_service import generate_greeting
from shared.v1.schemas import GreetingResponse

# 创建此模块专用的路由器
router = APIRouter(prefix="/greeting", tags=["Greeting"])

@router.get("/hello", response_model=GreetingResponse)
async def say_hello(name: str = "World"):
    """
    API 端点：生成问候语。

    Args:
        name (str): 查询参数，要问候的名字。

    Returns:
        GreetingResponse: 包含问候语的响应模型。
    """
    try:
        # 调用核心服务层的业务逻辑函数
        result = await generate_greeting(name)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating greeting: {str(e)}")