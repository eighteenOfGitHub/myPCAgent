"""
backend/core/services/greeting_service.py

问候服务模块。

此模块包含与问候相关的业务逻辑函数，与 API 框架无关。
"""
from typing import Dict, Any

async def generate_greeting(name: str = "World") -> Dict[str, Any]:
    """
    核心业务逻辑：生成问候语。

    Args:
        name (str): 要问候的名字，默认为 "World"。

    Returns:
        Dict[str, Any]: 包含问候语的字典。
    """
    greeting_message = f"Hello, {name}! Welcome to PCAgent!"
    return {"message": greeting_message}
