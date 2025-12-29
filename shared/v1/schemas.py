"""
shared/v1/schemas.py

共享的 Pydantic 模型。

此模块定义了前后端共享的数据模型，包括 API 请求和响应模型。
"""
from pydantic import BaseModel

class GreetingResponse(BaseModel):
    message: str
