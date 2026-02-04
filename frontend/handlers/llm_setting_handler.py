# frontend/handlers/llm_setting_handler.py

import requests
from typing import Optional, List, Tuple
from config.env_config import env_config
from shared.llm_setting_schemas import (
    LLMConfigCreate,
    LLMProvider,
    LLMTestResponse,
    LLMConfigResponse,
    LLMConfigBasicResponse,
)
from shared.default_setting_schemas import DefaultSettingResponse, SetDefaultLLMResponse

# 重要过程：从 env_config 统一获取 API 基址
API_BASE = env_config.API_BASE_URL

def submit_new_llm_config(
    provider: LLMProvider,
    model_name: str,
    api_key: str | None,
    base_url: Optional[str] = None
) -> tuple[bool, str]:
    """Handler for 'Submit' button to save new LLM configuration."""
    if provider == LLMProvider.OLLAMA and api_key is None:
        api_key = ""
    
    # 提交前加密 api_key
    from shared.crypto import encrypt_text
    encrypted_api_key = encrypt_text(api_key) if api_key else ""
        
    config_data = LLMConfigCreate(
        provider=provider,
        model_name=model_name,
        api_key=encrypted_api_key,
        base_url=base_url
    )

    try:
        response = requests.post(
            url=f"{API_BASE}/settings/llm",
            json=config_data.model_dump(),
            timeout=30
        )

        if response.status_code == 200:
            saved_config = LLMConfigResponse.model_validate(response.json())
            return True, f"模型 '{saved_config.model_name}' 配置已成功保存！"
        else:
            error_detail = _get_error_detail(response)
            return False, f"请求失败: {error_detail}"

    except requests.exceptions.Timeout:
        return False, "请求超时，请检查网络或服务器状态。"
    except requests.exceptions.ConnectionError:
        return False, "无法连接到后端服务器，请确认后端服务已启动。"
    except Exception as e:
        return False, f"发生未知错误: {str(e)}"

def test_existing_llm_config(config_id: int) -> str:
    """Handler for '🟢 Test' button on an existing config row."""
    try:
        response = requests.post(
            url=f"{API_BASE}/settings/llm/{config_id}/test",
            timeout=30
        )
        if response.status_code == 200:
            result = LLMTestResponse.model_validate(response.json())
            return result.message or ("测试通过" if result.success else "测试失败")
        else:
            error_detail = _get_error_detail(response)
            return f"测试失败: {error_detail}"
    except Exception as e:
        return f"测试时发生错误: {str(e)}"

def delete_llm_config(config_id: int) -> bool:
    """Handler for '🗑️ Delete' button on an existing config row."""
    try:
        response = requests.delete(
            url=f"{API_BASE}/settings/llm/{config_id}",
            timeout=10
        )
        if response.status_code == 200:
            from shared.general_schemas import MessageResponse
            MessageResponse.model_validate(response.json())
            return True
        return False
    except Exception:
        return False

def get_all_llm_configs() -> tuple[bool, list | str]:
    """Handler function to fetch all LLM configurations from the backend API."""
    try:
        response = requests.get(
            url=f"{API_BASE}/settings/llm/",
            timeout=30
        )

        if response.status_code == 200:
            configs_list = [LLMConfigResponse.model_validate(cfg) for cfg in response.json()]
            return True, [cfg.model_dump() for cfg in configs_list]
        else:
            error_detail = _get_error_detail(response)
            return False, f"获取配置列表失败: {error_detail}"

    except requests.exceptions.Timeout:
        return False, "请求超时，请检查网络或服务器状态。"
    except requests.exceptions.ConnectionError:
        return False, "无法连接到后端服务器，请确认后端服务已启动。"
    except requests.exceptions.RequestException as e:
        return False, f"请求发生错误: {str(e)}"
    except Exception as e:
        return False, f"发生未知错误: {str(e)}"

def fetch_llm_basic_options() -> List[Tuple[str, int]]:
    """获取下拉可选项，返回 [(label, id), ...]"""
    try:
        resp = requests.get(f"{API_BASE}/settings/llm/basic", timeout=10)
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
        resp = requests.get(f"{API_BASE}/preference", timeout=10)
        resp.raise_for_status()
        pref = DefaultSettingResponse.model_validate(resp.json())
        return pref.default_llm_config_id
    except Exception:
        return None

def set_default_llm_config(config_id: int | None) -> tuple[bool, str, int | None]:
    """保存默认 LLM 配置，config_id 为 None 表示清空。"""
    try:
        params = {"config_id": config_id} if config_id is not None else {}
        resp = requests.post(f"{API_BASE}/preference/default-llm", params=params, timeout=10)
        resp.raise_for_status()
        result = SetDefaultLLMResponse.model_validate(resp.json())
        return True, "Saved default model successfully.", result.default_llm_config_id
    except Exception as e:
        return False, f"Save default model failed: {e}", None

def _get_error_detail(response):
    try:
        return response.json().get("detail", f"HTTP Error: {response.status_code}")
    except ValueError:
        return f"HTTP Error: {response.status_code}, Response Text: {response.text}"

def format_ts_to_sec(value):
    if not value:
        return value
    if isinstance(value, str):
        return value[:19].replace("T", " ")
    try:
        return value.strftime("%Y-%m-%d %H:%M:%S")
    except Exception:
        return value

def normalize_provider_label(provider):
    if hasattr(provider, "value"):
        return provider.value
    if isinstance(provider, str) and provider.startswith("LLMProvider."):
        return provider.split(".", 1)[1].title()
    return str(provider) if provider is not None else ""

def build_choices_from_configs(configs, default_id):
    choices = []
    for cfg in configs or []:
        provider_label = normalize_provider_label(cfg.get("provider"))
        label = f"{provider_label} / {cfg.get('model_name')}"
        choices.append((label, cfg.get("id")))
    if not default_id:
        return choices
    marked = []
    for label, value in choices:
        if value == default_id:
            label = f"{label}(default model)"
        marked.append((label, value))
    return marked

def build_delete_choices(configs):
    choices = []
    for cfg in configs or []:
        provider_label = normalize_provider_label(cfg.get("provider"))
        label = f"{cfg.get('model_name')} ({provider_label}) [ID: {cfg.get('id')}]"
        choices.append((label, cfg.get("id")))
    return choices

def get_selected_default(choices, default_id):
    if choices and any(c[1] == default_id for c in choices):
        return default_id
    return choices[0][1] if choices else None

def build_rows_from_configs(configs, default_id):
    rows = []
    for config in configs or []:
        row_id = config.get("id")
        rows.append([
            row_id,
            config.get("provider"),
            config.get("model_name"),
            "√" if (row_id is not None and default_id is not None and str(row_id) == str(default_id)) else "",
            config.get("base_url"),
            format_ts_to_sec(config.get("updated_at")),
        ])
    return rows

def fetch_llm_state():
    configs = []
    success, data_or_error = get_all_llm_configs()
    if success and isinstance(data_or_error, list):
        configs = data_or_error
    default_id = fetch_default_llm_config_id()
    return configs, default_id