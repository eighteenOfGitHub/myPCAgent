import requests
from typing import Optional
from shared.llm_setting import LLMConfigCreate, LLMProvider, LLMTestResponse, LLMConfigResponse
from shared.crypto import encrypt_text

def submit_new_llm_config(
    provider: LLMProvider,
    model_name: str,
    api_key: str | None,
    base_url: Optional[str] = None
) -> tuple[bool, str]:
    """Handler for 'Submit' button to save new LLM configuration."""
    if provider == LLMProvider.OLLAMA and api_key is None:
        api_key = ""
    encrypted_api_key = encrypt_text(api_key)
        
    config_data = LLMConfigCreate(
        provider=provider,
        model_name=model_name,
        api_key=encrypted_api_key,
        base_url=base_url
    )

    try:
        response = requests.post(
            url="http://localhost:8000/api/settings/llm",
            json=config_data.model_dump(),
            timeout=60
        )

        if response.status_code == 200:
            # 使用 LLMConfigResponse 验证响应
            saved_config = LLMConfigResponse.model_validate(response.json())
            return True, f"模型 '{saved_config.model_name}' 配置已成功保存！"
        else:
            error_detail = response.json().get("detail", f"HTTP Error: {response.status_code}")
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
            url=f"http://localhost:8000/api/settings/llm/{config_id}/test",
            timeout=30
        )
        if response.status_code == 200:
            # 使用 LLMTestResponse 验证响应
            result = LLMTestResponse.model_validate(response.json())
            return result.message or ("测试通过" if result.success else "测试失败")
        else:
            error_detail = response.json().get("detail", f"HTTP Error: {response.status_code}")
            return f"测试失败: {error_detail}"
    except Exception as e:
        return f"测试时发生错误: {str(e)}"

def delete_llm_config(config_id: int) -> bool:
    """Handler for '🗑️ Delete' button on an existing config row."""
    try:
        response = requests.delete(
            url=f"http://localhost:8000/api/settings/llm/{config_id}",
            timeout=10
        )
        if response.status_code == 200:
            # 虽然 MessageResponse 可选，但建议验证
            from shared.schemas import MessageResponse
            MessageResponse.model_validate(response.json())
            return True
        return False
    except Exception:
        return False

def get_all_llm_configs() -> tuple[bool, list | str]:
    """Handler function to fetch all LLM configurations from the backend API."""
    try:
        response = requests.get(
            url="http://localhost:8000/api/settings/llm/",
            timeout=30
        )

        if response.status_code == 200:
            # 使用 LLMConfigResponse 逐个验证列表中的配置
            configs_list = [LLMConfigResponse.model_validate(cfg) for cfg in response.json()]
            return True, [cfg.model_dump() for cfg in configs_list]
        else:
            try:
                error_detail = response.json().get("detail", f"HTTP Error: {response.status_code}")
            except ValueError:
                error_detail = f"HTTP Error: {response.status_code}, Response Text: {response.text}"
            return False, f"获取配置列表失败: {error_detail}"

    except requests.exceptions.Timeout:
        return False, "请求超时，请检查网络或服务器状态。"
    except requests.exceptions.ConnectionError:
        return False, "无法连接到后端服务器，请确认后端服务已启动。"
    except requests.exceptions.RequestException as e:
        return False, f"请求发生错误: {str(e)}"
    except Exception as e:
        return False, f"发生未知错误: {str(e)}"