# frontend/handers/dashboard.py
import requests
from config.env_config import env_config

def handle_hello_request():
    """处理向后端发送 hello 请求的函数。"""
    api_url = f"{env_config.API_BASE_URL}/greeting/hello"

    try:
        response = requests.get(api_url)
        response.raise_for_status()
        data = response.json()
        # 假设 GreetingResponse 模型是 {"message": "..."}
        backend_message = data.get("message", "未收到后端消息")
        print(f"[DEBUG] 后端返回数据: {data}, 提取消息: {backend_message}")
        return ("发送 Hello 请求", backend_message)

    except Exception as e:
        error_msg = f"请求后端失败: {e}"
        print(error_msg)
        return ("发送 Hello 请求", error_msg)

def update_chat_with_hello(history):
    """
    处理按钮点击事件，调用后端请求并更新聊天历史。
    返回一个符合 Gradio Chatbot 格式的字典列表。
    """
    print(f"[DEBUG] 当前历史: {history}")
    user_msg, bot_reply = handle_hello_request()
    
    print(f"[DEBUG] 用户消息: {user_msg}, 机器人回复: {bot_reply}")
    
    # 确保创建一个全新的列表对象
    new_user_message = {"role": "user", "content": user_msg}
    new_bot_message = {"role": "assistant", "content": bot_reply}
    
    # 将新消息对添加到历史记录
    new_history = history + [new_user_message, new_bot_message]
    
    print(f"[DEBUG] 新历史: {new_history}")
    
    # 返回新的列表对象
    return new_history, new_history