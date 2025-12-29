"""
backend/api/v1/api_router.py

API 路由聚合器。

此模块定义了 v1 版本 API 的主路由器，并可以在此处包含其他子路由器。
"""
from fastapi import APIRouter

from backend.api.v1.endpoints import greeting

router = APIRouter(tags=["v1"])

router.include_router(greeting.router)