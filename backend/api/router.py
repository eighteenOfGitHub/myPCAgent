# backend/api/router.py

from fastapi import APIRouter

from backend.api.endpoints import chat_api, default_setting_api, greeting_api, llm_setting_api
from backend.api.endpoints import health_api  


router = APIRouter()

router.include_router(greeting_api.router)
router.include_router(health_api.router)
router.include_router(chat_api.router)
router.include_router(default_setting_api.router)
router.include_router(llm_setting_api.router)




