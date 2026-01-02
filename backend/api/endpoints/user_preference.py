# backend/api/endpoints/user_preference.py
from fastapi import APIRouter, HTTPException
from typing import Optional
from backend.services.user_preference_service import UserPreferenceService
from backend.db_models.user_config import UserPreference

router = APIRouter(prefix="/preference", tags=["User Preference"])


@router.get("", response_model=UserPreference)
def get_user_preference():
    """获取当前用户偏好设置"""
    service = UserPreferenceService()
    try:
        pref = service.get_preference()
        return pref
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取偏好失败: {str(e)}")


@router.post("/default-llm")
def set_default_llm_config(config_id: Optional[int] = None):
    """
    设置默认 LLM 配置
    - config_id: LLMConfig 的 ID，None 表示清空默认
    """
    service = UserPreferenceService()
    try:
        updated = service.update_default_llm_config(config_id)
        return {
            "status": "success",
            "default_llm_config_id": updated.default_llm_config_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存偏好失败: {str(e)}")