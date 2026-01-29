"""
backend/api/router.py

API 路由聚合器。
"""
from fastapi import APIRouter

from backend.api.endpoints import chat_api, greeting_api, llm_setting_api, user_preference_api
from backend.api.endpoints import health_api  


router = APIRouter()

router.include_router(greeting_api.router)
router.include_router(health_api.router)
router.include_router(chat_api.router)
router.include_router(user_preference_api.router)
router.include_router(llm_setting_api.router)




