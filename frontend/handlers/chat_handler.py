# frontend/handlers/chat_handler.py
import requests
import json
from typing import Generator, Tuple, List, Any
import gradio as gr

from config.env_config import env_config

# 后端 API 基础 URL
API_BASE = f"http://{env_config.BACKEND_HOST}:{env_config.BACKEND_PORT}/api"

def _handle_api_error(e: Exception) -> str:
    """统一错误处理"""
    if isinstance(e, requests.exceptions.ConnectionError):
        return "[ERROR: 无法连接后端服务，请检查 FastAPI 是否运行]"
    elif isinstance(e, requests.exceptions.Timeout):
        return "[ERROR: 请求超时]"
    elif isinstance(e, requests.exceptions.HTTPError):
        return f"[ERROR: HTTP {e.response.status_code}]"
    else:
        return f"[ERROR: {str(e)}]"

def load_session_list() -> List[Tuple[str, int]]:
    """加载会话列表用于 Dropdown"""
    try:
        resp = requests.get(f"{API_BASE}/chat/sessions", timeout=5)
        resp.raise_for_status()
        sessions = resp.json()
        return [(s.get("title") or f"会话 {s['id']}", s["id"]) for s in sessions]
    except Exception as e:
        print(f"加载会话列表失败: {e}")
        return []

def create_new_session() -> Tuple[Any, int, List, List]:
    """创建新会话"""
    try:
        # 默认使用第一个 LLM 配置（你可根据需求调整）
        resp = requests.post(
            f"{API_BASE}/chat/sessions",
            json={"title": "新会话", "config_id": 1},
            timeout=10
        )
        resp.raise_for_status()
        new_sess = resp.json()
        
        # 刷新会话列表
        session_choices = load_session_list()
        
        return (
            gr.Dropdown(choices=session_choices, value=new_sess["id"]),
            new_sess["id"],
            [],  # chat history state
            []   # chatbot display
        )
    except Exception as e:
        error_msg = _handle_api_error(e)
        return (
            gr.Dropdown(),
            None,
            [],
            [(error_msg, "")]
        )

def load_messages(session_id: int) -> Tuple[List, List]:
    """加载指定会话的消息历史"""
    if not session_id:
        return [], []
    
    try:
        resp = requests.get(f"{API_BASE}/chat/sessions/{session_id}/messages", timeout=5)
        resp.raise_for_status()
        messages = resp.json()
        
        # 转换为 Gradio Chatbot 格式 [(user, bot), ...]
        history = []
        user_msg = None
        for msg in messages:
            if msg["role"] == "user":
                user_msg = msg["content"]
            elif msg["role"] == "assistant" and user_msg is not None:
                history.append((user_msg, msg["content"]))
                user_msg = None
        
        return history, history
    except Exception as e:
        error_msg = _handle_api_error(e)
        return [(error_msg, "")], [(error_msg, "")]

def stream_chat(session_id: int, user_message: str, history: List) -> Generator:
    """流式发送消息并生成响应"""
    if not session_id:
        yield [(f"[ERROR: 请先创建或选择一个会话]", "")]
        return
    
    # 先显示用户消息
    history.append((user_message, ""))
    yield history

    full_reply = ""
    try:
        with requests.post(
            f"{API_BASE}/chat/stream",
            json={"session_id": session_id, "user_message": user_message},
            stream=True,
            timeout=60
        ) as r:
            r.raise_for_status()
            for line in r.iter_lines():
                if line:
                    if line.startswith(b"data: "):
                        token = line[6:].decode()
                        if token.startswith("[ERROR:"):
                            full_reply = token
                            break
                        full_reply += token
                        history[-1] = (user_message, full_reply)
                        yield history
    except Exception as e:
        error_msg = _handle_api_error(e)
        history[-1] = (user_message, error_msg)
        yield history