import requests
from config.env_config import env_config
from shared.greeting import GreetingResponse

def handle_hello_request():
    """处理向后端发送 hello 请求的函数。"""
    api_url = f"{env_config.API_BASE_URL}/greeting/hello"

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        # 使用 GreetingResponse 验证响应
        data = GreetingResponse.model_validate(response.json())
        return ("发送 Hello 请求", data.message)

    except Exception as e:
        error_msg = f"请求后端失败: {e}"
        print(error_msg)
        return ("发送 Hello 请求", error_msg)

def update_chat_with_hello(history):
    """使用 hello 响应更新聊天历史"""
    title, message = handle_hello_request()
    history.append((title, message))
    return history