# frontend/handlers/llm_models_setting.py

import requests
from typing import Optional
from shared.schemas import LLMConfigCreate, LLMProvider, LLMTestResponse, LLMConfigResponse


def submit_new_llm_config(
    provider: LLMProvider,
    model_name: str,
    api_key: str | None,
    base_url: Optional[str] = None
) -> tuple[bool, str]:  # 返回 (success, message)
    """
    Handler for 'Submit' button to save new LLM configuration.
    Returns (True, "Success message") if successful.
    Returns (False, "Error message") if failed.
    """
    if provider == LLMProvider.OLLAMA and api_key is None:
        api_key = ""
        
    config_data = LLMConfigCreate(
        provider=provider,
        model_name=model_name,
        api_key=api_key,
        base_url=base_url
    )

    try:
        # 调用后端 API：先测试连通性，成功则保存
        response = requests.post(
            url="http://localhost:8000/api/settings/llm",  # 新增的 API 端点
            json=config_data.model_dump(),  # 将 Pydantic 模型转为字典
            timeout=30  # 设置超时时间
        )

        if response.status_code == 200:
            # 如果成功 (HTTP 200)，FastAPI 会返回 LLMConfig 的 JSON
            saved_config: LLMConfigResponse = LLMConfigResponse.model_validate(response.json())
            return True, f"模型 '{saved_config.model_name}' 配置已成功保存！"
        else:
            # 处理 HTTP 错误，包括 400 Bad Request (测试失败或输入错误)
            error_detail = response.json().get("detail", f"HTTP Error: {response.status_code}")
            return False, f"请求失败: {error_detail}"

    except requests.exceptions.Timeout:
        return False, "请求超时，请检查网络或服务器状态。"
    except requests.exceptions.ConnectionError:
        return False, "无法连接到后端服务器，请确认后端服务已启动。"
    except requests.exceptions.RequestException as e:
        return False, f"请求发生错误: {str(e)}"
    except Exception as e:
        return False, f"发生未知错误: {str(e)}"


def test_existing_llm_config(config_id: int) -> str:
    """
    Handler for '🟢 Test' button on an existing config row.
    Returns test result message.
    """
    try:
        response = requests.post(
            url=f"http://localhost:8000/api/settings/llm/{config_id}/test",  # 测试现有配置的 API
            timeout=30
        )
        if response.status_code == 200:
            result: LLMTestResponse = LLMTestResponse.model_validate(response.json())
            return result.message or ("测试通过" if result.success else "测试失败")
        else:
            error_detail = response.json().get("detail", f"HTTP Error: {response.status_code}")
            return f"测试失败: {error_detail}"
    except Exception as e:
        return f"测试时发生错误: {str(e)}"


def delete_llm_config(config_id: int) -> bool:
    """
    Handler for '🗑️ Delete' button on an existing config row.
    Returns True if deletion succeeded.
    """
    try:
        response = requests.delete(
            url=f"http://localhost:8000/api/settings/llm/{config_id}",
            timeout=10
        )
        return response.status_code == 200
    except Exception:
        return False