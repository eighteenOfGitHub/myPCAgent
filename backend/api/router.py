"""
backend/api/router.py

API 路由聚合器。
"""
from fastapi import APIRouter

from backend.api.endpoints import greeting
from backend.api.endpoints import greeting, health, chat  

router = APIRouter()

router.include_router(greeting.router)
router.include_router(health.router)
router.include_router(chat.router)




