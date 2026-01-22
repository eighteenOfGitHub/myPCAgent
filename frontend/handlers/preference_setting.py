import os
from typing import List, Tuple, Optional
import requests
from shared.llm_setting import LLMConfigBasicResponse
from shared.user_preference import UserPreferenceResponse

API_BASE = os.getenv("BACKEND_API_BASE", "http://127.0.0.1:8000/api")
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
