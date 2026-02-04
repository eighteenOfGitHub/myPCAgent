# backend/api/endpoints/default_setting_api.py

from fastapi import APIRouter, HTTPException
from typing import Optional

from backend.services.default_setting_service import DefaultSettingService
from backend.db_models.setting_models import DefaultSetting
from shared.default_setting_schemas import DefaultSettingResponse, SetDefaultLLMResponse

router = APIRouter(prefix="/preference", tags=["Default Settings"])


@router.get("", response_model=DefaultSettingResponse)
def get_default_setting():
    """获取当前默认设置"""
    service = DefaultSettingService()
    try:
        setting = service.get_setting()
        return setting
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取默认设置失败: {str(e)}")


@router.post("/default-llm", response_model=SetDefaultLLMResponse)
def set_default_llm_config(config_id: Optional[int] = None):
    """
    设置默认 LLM 配置
    - config_id: LLMConfig 的 ID，None 表示清空默认
    """
    service = DefaultSettingService()
    try:
        updated = service.update_default_llm_config(config_id)
        return {
            "status": "success",
            "default_llm_config_id": updated.default_llm_config_id
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存默认设置失败: {str(e)}")