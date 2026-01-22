# backend/api/endpoints/llm_setting.py

from fastapi import APIRouter, HTTPException
from typing import List
from backend.services.llm_setting_service import LLMSettingService
from shared.llm_setting import (
    LLMConfigCreate,
    LLMConfigResponse,
    LLMConfigBasicResponse,
    LLMTestResponse,
)

router = APIRouter(prefix="/settings/llm", tags=["llm-setting"])

@router.post("", response_model=LLMConfigResponse) # 保留原来的 response_model
def create_llm_config(
    config_data: LLMConfigCreate, # 使用 Pydantic 模型接收请求体
):
    """
    测试 LLM 连通性，如果成功则创建并保存配置。
    """
    service = LLMSettingService()
    try:
        # 1. 先测试连通性
        test_result = service.test_connection(
            provider=config_data.provider.value, # 转换为字符串
            model_name=config_data.model_name,
            api_key_input=config_data.api_key,
            base_url=config_data.base_url
        )
        
        if not test_result["success"]:
            # 如果测试失败，抛出 HTTPException
            raise HTTPException(status_code=400, detail=test_result["message"])

        # 2. 测试成功，调用 service 的 create 方法保存
        saved_config = service.create(
            provider=config_data.provider.value, # 转换为字符串
            model_name=config_data.model_name,
            api_key_input=config_data.api_key,
            base_url=config_data.base_url
        )
        
        # 3. 测试成功且保存成功，返回保存的配置信息 (LLMConfig)
        # FastAPI 会自动将 LLMConfig 对象序列化为 JSON
        return LLMConfigResponse.model_validate(saved_config, from_attributes=True)

    except HTTPException:
        # 如果是 HTTPException，直接抛出，FastAPI 会处理
        raise
    except ValueError as e:
        # 处理 service.create 可能抛出的 ValueError
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        # 处理其他意外错误
        raise HTTPException(status_code=500, detail=f"创建 LLM 配置失败: {str(e)}")

# --- 新增：测试现有配置接口 ---
@router.post("/{config_id}/test", response_model=LLMTestResponse)  # 响应模型使用专用的 LLMTestResponse
def test_existing_config(config_id: int):
    """
    测试一个已存在的 LLM 配置。
    """
    service = LLMSettingService()
    try:
        config = service.get_by_id(config_id)
        if not config:
            raise HTTPException(status_code=404, detail="LLM 配置不存在")
        
        test_result = service.test_connection(
            provider=config.provider,
            model_name=config.model_name,
            api_key_input=config.api_key, # 注意：这里使用数据库中存储的 key
            base_url=config.base_url
        )
        
        if test_result["success"]:
            return {"success": True, "message": test_result["message"]}
        else:
            # 测试失败，抛出 HTTPException
            raise HTTPException(status_code=400, detail=test_result["message"])
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"测试 LLM 配置失败: {str(e)}")

# --- 保留原有的其他接口 ---
@router.get("", response_model=List[LLMConfigResponse])
def list_llm_configs():
    """列出所有 LLM 配置"""
    service = LLMSettingService()
    try:
        configs = service.get_all()
        return [LLMConfigResponse.model_validate(c, from_attributes=True) for c in configs]
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 LLM 配置列表失败: {str(e)}")

@router.get("/basic", response_model=List[LLMConfigBasicResponse])
def list_basic_llm_configs():
    """仅返回基础字段（id/provider/model_name），用于下拉选择。"""
    service = LLMSettingService()
    try:
        return service.list_basic_configs()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取 LLM 基础配置失败: {str(e)}")

@router.get("/{config_id}", response_model=LLMConfigResponse)
def get_llm_config(config_id: int):
    """获取指定 ID 的 LLM 配置"""
    service = LLMSettingService()
    config = service.get_by_id(config_id)
    if not config:
        raise HTTPException(status_code=404, detail="LLM 配置不存在")
    return LLMConfigResponse.model_validate(config, from_attributes=True)

@router.delete("/{config_id}")
def delete_llm_config(config_id: int):
    """删除指定 ID 的 LLM 配置"""
    service = LLMSettingService()
    deleted = service.delete(config_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="LLM 配置不存在或已删除")
    return {"status": "success", "message": f"配置 {config_id} 已删除"}