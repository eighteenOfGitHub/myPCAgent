import os
from typing import List, Tuple
import requests
from shared.llm_setting import LLMConfigBasicResponse

API_BASE = os.getenv("BACKEND_API_BASE", "http://127.0.0.1:8000/api")
LLM_BASIC_ENDPOINT = f"{API_BASE}/settings/llm/basic"


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
