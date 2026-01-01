"""backend/api/endpoints/chat.py

聊天相关的所有 API 端点。
"""

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from typing import List

from shared.schemas import (
    ChatSessionCreate,
    ChatSessionRead,
    ChatMessageRead,
    ChatTurnRequest,
    ChatTurnResponse,
)
from backend.core.services.chat_service import ChatService


router = APIRouter(prefix="/chat", tags=["Chat"])


def get_chat_service():
    service = ChatService()
    try:
        yield service
    finally:
        service.close()


@router.post("/sessions", response_model=ChatSessionRead)
async def create_session(
    session_create: ChatSessionCreate,
    service: ChatService = Depends(get_chat_service),
):
    try:
        session = service.create_session(
            title=session_create.title,
            config_id=session_create.config_id,
        )
        return session
    except Exception as e:
        # 更精细的错误可后续拆分
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/sessions", response_model=List[ChatSessionRead])
async def list_sessions(service: ChatService = Depends(get_chat_service)):
    try:
        sessions = service.list_sessions()
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取会话列表失败: {str(e)}")


@router.get("/sessions/{session_id}", response_model=ChatSessionRead)
async def get_session(
    session_id: int,
    service: ChatService = Depends(get_chat_service),
):
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    return session


@router.get("/sessions/{session_id}/messages", response_model=List[ChatMessageRead])
async def get_messages(
    session_id: int,
    service: ChatService = Depends(get_chat_service),
):
    if not service.get_session(session_id):
        raise HTTPException(status_code=404, detail="会话不存在")
    messages = service.get_session_messages(session_id)
    return messages


@router.post("/turn", response_model=ChatTurnResponse)
async def chat_turn(
    request: ChatTurnRequest,
    service: ChatService = Depends(get_chat_service),
):
    try:
        response = service.chat_turn(
            session_id=request.session_id,
            user_message=request.user_message,
        )
        return response
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"LLM 调用失败: {str(e)}")


@router.post("/stream")
async def chat_stream(
    request: ChatTurnRequest,
    service: ChatService = Depends(get_chat_service),
):
    # 验证会话存在
    if not service.get_session(request.session_id):
        raise HTTPException(status_code=404, detail="会话不存在")

    # 先保存用户消息
    service._save_message(request.session_id, "user", request.user_message)

    full_reply = ""

    async def event_generator():
        nonlocal full_reply
        try:
            for token in service.chat_turn_stream(request.session_id, request.user_message):
                if token.startswith("[ERROR:"):
                    yield f"data: {token}\n\n"
                    break
                full_reply += token
                yield f"data: {token}\n\n"
        finally:
            # 流结束后保存助手完整回复（仅当无错误）
            if full_reply and not full_reply.startswith("[ERROR:"):
                service._save_message(request.session_id, "assistant", full_reply)
                # 更新会话更新时间
                session = service.get_session(request.session_id)
                if session:
                    from datetime import datetime
                    session.updated_at = datetime.utcnow()
                    service._session.add(session)
                    service._session.commit()

    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: int,
    service: ChatService = Depends(get_chat_service),
):
    session = service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="会话不存在")
    service._session.delete(session)
    service._session.commit()
    return {"message": "会话已删除"}