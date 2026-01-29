# frontend/handlers/chat_handler.py

import requests
import json
from typing import Generator, Tuple, List, Any
import gradio as gr

from config.env_config import env_config
from shared.chat_schemas import ChatSessionCreate, ChatSessionRead, ChatMessageRead, ChatTurnResponse
from shared.general_schemas import MessageResponse

# 重要过程：从 env_config 统一获取 API 基址
API_BASE = env_config.API_BASE_URL

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
        # 使用 ChatSessionRead 验证响应格式
        sessions = [ChatSessionRead.model_validate(s) for s in resp.json()]
        return [(s.title or f"会话 {s.id}", s.id) for s in sessions]
    except Exception as e:
        print(f"加载会话列表失败: {e}")
        return []

def create_new_session() -> Tuple[Any, int, List, List]:
    """创建新会话"""
    try:
        resp = requests.post(
            f"{API_BASE}/chat/sessions",
            json=ChatSessionCreate(title="新会话", config_id=1).model_dump(),
            timeout=10
        )
        resp.raise_for_status()
        # 使用 ChatSessionRead 验证响应
        new_sess = ChatSessionRead.model_validate(resp.json())
        
        session_choices = load_session_list()
        
        return (
            gr.Dropdown(choices=session_choices, value=new_sess.id),
            new_sess.id,
            [],
            []
        )
    except Exception as e:
        error_msg = _handle_api_error(e)
        return (gr.Dropdown(), None, [], [(error_msg, "")])

def load_messages(session_id: int) -> Tuple[List, List]:
    """加载指定会话的消息历史"""
    try:
        resp = requests.get(f"{API_BASE}/chat/sessions/{session_id}/messages", timeout=5)
        resp.raise_for_status()
        # 使用 ChatMessageRead 验证响应
        messages = [ChatMessageRead.model_validate(m) for m in resp.json()]
        
        history = []
        chat_display = []
        for msg in messages:
            if msg.role == "user":
                history.append((msg.content, ""))
                chat_display.append((msg.content, ""))
            elif msg.role == "assistant":
                if history:
                    history[-1] = (history[-1][0], msg.content)
                chat_display.append(("", msg.content))
        
        return history, chat_display
    except Exception as e:
        print(f"加载消息失败: {e}")
        return [], []

def stream_chat(session_id: int, user_message: str, history: List) -> Generator:
    """流式发送消息并生成响应"""
    if not session_id:
        yield [(f"[ERROR: 请先创建或选择一个会话]", "")]
        return
    
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