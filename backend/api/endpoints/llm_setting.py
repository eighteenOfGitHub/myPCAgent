# backend/api/endpoints/llm_setting.py
from fastapi import APIRouter, HTTPException, Body
from typing import List, Optional
from backend.services.llm_setting_service import LLMSettingService
from backend.db_models.user_config import LLMConfig

router = APIRouter(prefix="/settings/llm")  # ← 关键：统一前缀


@router.post("", response_model=LLMConfig)
def create_llm_config(
    provider: str = Body(..., embed=True),
    model_name: str = Body(..., embed=True),
    api_key: str = Body(..., embed=True),
    base_url: Optional[str] = Body(None, embed=True),
):
    """创建一个新的 LLM 配置"""
    service = LLMSettingService()
    try:
        config = service.create(
            provider=provider,
            model_name=model_name,
            api_key_input=api_key,
            base_url=base_url,
        )
        return config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建 LLM 配置失败: {str(e)}")


@router.put("/{config_id}", response_model=LLMConfig)
def update_llm_config(
    config_id: int,
    provider: Optional[str] = Body(None, embed=True),
    model_name: Optional[str] = Body(None, embed=True),
    api_key: Optional[str] = Body(None, embed=True),
    base_url: Optional[str] = Body(None, embed=True),
):
    """更新指定 ID 的 LLM 配置"""
    service = LLMSettingService()
    try:
        config = service.update(
            config_id=config_id,
            provider=provider,
            model_name=model_name,
            api_key_input=api_key,
            base_url=base_url,
        )
        return config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新 LLM 配置失败: {str(e)}")


@router.get("", response_model=List[LLMConfig])
def list_llm_configs():
    """列出所有 LLM 配置（供前端下拉选择）"""
    service = LLMSettingService()
    try:
        configs = service.get_all()
        return configs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 LLM 配置列表失败: {str(e)}")


@router.get("/{config_id}", response_model=LLMConfig)
def get_llm_config(config_id: int):
    """获取指定 ID 的 LLM 配置"""
    service = LLMSettingService()
    config = service.get_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="LLM 配置不存在")
    return config


@router.delete("/{config_id}")
def delete_llm_config(config_id: int):
    """删除指定 ID 的 LLM 配置"""
    service = LLMSettingService()
    deleted = service.delete(config_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="LLM 配置不存在或已删除")
    return {"status": "success", "message": f"配置 {config_id} 已删除"}