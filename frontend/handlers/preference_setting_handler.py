import os
from typing import List, Tuple, Optional
import requests
from config.env_config import env_config
from shared.llm_setting_schemas import LLMConfigBasicResponse
from shared.user_preference_schemas import UserPreferenceResponse, SetDefaultLLMResponse

# 重要过程：从 env_config 统一获取 API 基址
API_BASE = env_config.API_BASE_URL
LLM_BASIC_ENDPOINT = f"{API_BASE}/settings/llm/basic"
USER_PREF_ENDPOINT = f"{API_BASE}/preference"


def fetch_llm_basic_options() -> List[Tuple[str, int]]:
    """获取下拉可选项，返回 [(label, id), ...]"""
    try:
        resp = requests.get(LLM_BASIC_ENDPOINT, timeout=10)
        resp.raise_for_status()
        items = resp.json()
        validated = [LLMConfigBasicResponse.model_validate(item) for item in items]
        return [
            (f"{item.provider.value} / {item.model_name}", item.id)
            for item in validated
        ]
    except Exception:
        return []


def fetch_default_llm_config_id() -> Optional[int]:
    """获取后端保存的默认 LLM 配置 ID，失败返回 None"""
    try:
        resp = requests.get(USER_PREF_ENDPOINT, timeout=10)
        resp.raise_for_status()
        pref = UserPreferenceResponse.model_validate(resp.json())
        return pref.default_llm_config_id
    except Exception:
        return None


def set_default_llm_config(config_id: Optional[int]) -> tuple[bool, str, Optional[int]]:
    """保存默认 LLM 配置，config_id 为 None 表示清空。"""
    try:
        params = {"config_id": config_id} if config_id is not None else {}
        resp = requests.post(f"{USER_PREF_ENDPOINT}/default-llm", params=params, timeout=10)
        resp.raise_for_status()
        result = SetDefaultLLMResponse.model_validate(resp.json())
        return True, "Saved default model successfully.", result.default_llm_config_id
    except Exception as e:
        return False, f"Save default model failed: {e}", None
