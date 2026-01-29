# shared/general_schemas.py
from pydantic import BaseModel
from typing import Optional, Any

class MessageResponse(BaseModel):
    """通用消息响应（用于删除、更新等操作）"""
    message: str

class HealthResponse(BaseModel):
    """健康检查响应"""
    status: str
    service: str
    database: str

class ErrorResponse(BaseModel):
    """错误响应（FastAPI 会自动处理，此处用于文档）"""
    detail: str

__all__ = ["MessageResponse", "HealthResponse", "ErrorResponse"]