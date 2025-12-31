"""backend/api/v1/endpoints/health.py

健康检查相关的 API 端点。
用于验证服务是否正常运行，包括数据库连接状态。
"""

from fastapi import APIRouter, HTTPException
from sqlalchemy import text
from backend.core.database import engine

# 创建此模块专用的路由器
router = APIRouter(prefix="/health", tags=["Health"])


@router.get("")
async def health_check():
    """
    健康检查端点。

    Returns:
        dict: 包含服务状态和数据库连接状态的响应。
    """
    try:
        # 尝试执行简单 SQL 查询验证数据库连接
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        db_status = "ok"
    except Exception as e:
        db_status = f"error: {str(e)}"

    return {
        "status": "healthy",
        "service": "PCAgent Backend",
        "database": db_status,
    }