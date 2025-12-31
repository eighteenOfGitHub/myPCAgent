"""
backend/api/v1/api_router.py

API 路由聚合器。

此模块定义了 v1 版本 API 的主路由器，并可以在此处包含其他子路由器。
"""
from fastapi import APIRouter

from backend.api.endpoints import greeting
from backend.api.endpoints import greeting, health

router = APIRouter()

router.include_router(greeting.router)
router.include_router(health.router)





