# backend/services/chat_service.py

import os
import logging
from typing import List, Optional, Generator
from datetime import datetime, timezone
from sqlalchemy import desc
from sqlmodel import select

from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
from langchain_ollama import ChatOllama

from shared.chat_schemas import ChatTurnResponse
from backend.db_models.chat_models import LLMSetting, ChatSession, ChatMessage
from backend.services import get_llm_setting_service
from backend.core.database import get_db_session



logger = logging.getLogger(__name__)

class ChatService:
    """
    聊天服务：支持完整响应与流式输出。
    所有状态从数据库读取，服务本身无状态。
    """

    TITLE_PROMPT = "请为以下用户的首条消息生成一个简短的会话标题，20 字以内，直接返回标题："

    def __init__(self):
        pass

    def _get_llm_client(self, config: LLMSetting):
        """根据配置创建 LangChain LLM 客户端（自动解密 API Key）"""
        llm_service = get_llm_setting_service()
        api_key = llm_service.get_decrypted_api_key(config.id)
        
        provider = config.provider.lower()
        
        # Ollama 不需要 API Key
        if provider == "ollama":
            return ChatOllama(
                model=config.model_name,
                base_url=config.base_url or "http://localhost:11434",
                temperature=0.7,
            )
        
        # 其他 provider 需要 API Key
        if not api_key:
            raise ValueError(f"LLM 配置 ID={config.id} 的 API Key 解密失败或为空")
        
        if provider == "openai":
            return ChatOpenAI(
                model=config.model_name,
                api_key=api_key,
                base_url=config.base_url,
                temperature=0.7,
            )
        # elif provider == "anthropic":
        #     return ChatAnthropic(
        #         model=config.model_name,
        #         api_key=api_key,
        #         temperature=0.7,
        #     )
        else:
            raise ValueError(f"不支持的 LLM 提供商: {config.provider}")

    def create_session(self, first_message: str, config_id: Optional[int] = None) -> ChatSession:
        """基于首条用户消息生成标题并创建会话"""
        user_first_message = (first_message or "").strip()
        llm_service = get_llm_setting_service()

        config = None
        if config_id is not None:
            config = llm_service.get_by_id(config_id)
        if config is None:
            config = llm_service.get_active()

        if config is None:
            raise ValueError("未找到可用的 LLM 配置")

        llm = self._get_llm_client(config)
        prompt = f"{self.TITLE_PROMPT}\n\n用户消息：{user_first_message or '新对话'}"
        response = llm.invoke([HumanMessage(content=prompt)])
        generated_title = (getattr(response, "content", "") or "").strip() or "新对话"

        session_obj = ChatSession(title=generated_title, config_id=config.id)
        with get_db_session() as session:
            session.add(session_obj)
            session.commit()
            session.refresh(session_obj)
        return session_obj

    def get_session(self, session_id: int) -> Optional[ChatSession]:
        with get_db_session() as session:
            return session.get(ChatSession, session_id)

    def list_sessions(self) -> List[ChatSession]:
        """获取所有聊天会话，按更新时间倒序排列"""
        with get_db_session() as session:
            statement = select(ChatSession).order_by(desc(ChatSession.updated_at))
            return session.exec(statement).all()

    def get_session_messages(self, session_id: int) -> List[ChatMessage]:
        with get_db_session() as session:
            statement = (
                select(ChatMessage)
                .where(ChatMessage.session_id == session_id)
                .order_by(ChatMessage.created_at)
            )
            return session.exec(statement).all()

    def _save_message(
        self,
        session_id: int,
        role: str,
        content: str,
        llm_provider: str,
        llm_model_name: str,
    ) -> ChatMessage:
        message = ChatMessage(
            session_id=session_id,
            role=role,
            content=content,
            llm_provider=llm_provider,
            llm_model_name=llm_model_name,
        )
        with get_db_session() as session:
            session.add(message)
            session.commit()
            session.refresh(message)
        return message

    def _build_history(self, session_id: int) -> list:
        """从数据库构建完整消息历史（LangChain 格式）"""
        history = []
        messages = self.get_session_messages(session_id)
        for msg in messages:
            if msg.role == "user":
                history.append(HumanMessage(content=msg.content))
            elif msg.role == "assistant":
                history.append(AIMessage(content=msg.content))
        return history

    # ======================
    # 非流式：完整响应
    # ======================
    def chat_turn(self, session_id: int, user_message: str, config_id:Optional[int] = None) -> ChatTurnResponse:
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"会话 ID {session_id} 不存在")
        
        llm_service = get_llm_setting_service()
        config = None
        if config_id is not None:
            config = llm_service.get_by_id(config_id)
        elif config is None:
            config = llm_service.get_active()

        if config is None:
            raise ValueError("未找到可用的 LLM 配置")
        
        # 1. 先保存用户消息（带快照）
        user_msg = self._save_message(
            session_id=session_id,
            role="user",
            content=user_message,
            llm_provider=config.provider,
            llm_model_name=config.model_name,
        )

        # 2. 构建完整历史（含刚保存的用户消息）
        history = self._build_history(session_id)  # ← 注意：不再传 current_user_msg

        # 3. 调用 LLM
        llm = self._get_llm_client(config)
        response = llm.invoke(history)
        assistant_reply = response.content

        # 4. 保存 AI 回复（带相同快照）
        assistant_msg = self._save_message(
            session_id=session_id,
            role="assistant",
            content=assistant_reply,
            llm_provider=config.provider,
            llm_model_name=config.model_name,
        )

        # 5. 更新会话时间
        session.updated_at = datetime.now(timezone.utc)
        with get_db_session() as db_session:
            db_session.add(session)
            db_session.commit()

        return ChatTurnResponse(
            session_id=session_id,
            message_id=assistant_msg.id,
            assistant_reply=assistant_reply,
        )

    # ======================
    # 流式：生成器
    # ======================
    def chat_turn_stream(
        self,
        session_id: int,
        user_message: str,
        config_id: Optional[int] = None,
    ) -> Generator[str, None, None]:
        session = self.get_session(session_id)
        if not session:
            logger.warning("chat_turn_stream session_missing session_id=%s", session_id)
            yield "[ERROR: 会话不存在]"
            return

        llm_service = get_llm_setting_service()
        config = None
        if config_id is not None:
            config = llm_service.get_by_id(config_id)
        if config is None:
            config = llm_service.get_active()
        if not config:
            logger.error("chat_turn_stream config_missing session_id=%s", session_id)
            yield "[ERROR: LLM 配置丢失]"
            return

        logger.debug(
            "chat_turn_stream start session_id=%s config_id=%s provider=%s model=%s prompt_len=%s",
            session_id, config.id, config.provider, config.model_name, len(user_message or ""),
        )

        try:
            self._save_message(
                session_id=session_id,
                role="user",
                content=user_message or "",
                llm_provider=config.provider,
                llm_model_name=config.model_name,
            )
        except Exception as e:
            logger.error("chat_turn_stream save_user_failed session_id=%s err=%s", session_id, e)
            yield f"[ERROR: 用户消息保存失败: {str(e)}]"
            return

        history = self._build_history(session_id)
        llm = self._get_llm_client(config)

        assistant_reply = ""
        try:
            for chunk in llm.stream(history):
                token = getattr(chunk, "content", "") or ""
                if token:
                    assistant_reply += token
                    yield token
        except Exception as e:
            logger.error("chat_turn_stream llm_stream_error session_id=%s err=%s", session_id, e)
            yield f"[ERROR: {str(e)}]"
            return

        if assistant_reply:
            self._save_message(
                session_id=session_id,
                role="assistant",
                content=assistant_reply,
                llm_provider=config.provider,
                llm_model_name=config.model_name,
            )
            session.updated_at = datetime.now(timezone.utc)
            with get_db_session() as db_session:
                db_session.add(session)
                db_session.commit()
            logger.debug(
                "chat_turn_stream completed session_id=%s reply_len=%s",
                session_id, len(assistant_reply),
            )

    def delete_session(self, session_id: int) -> bool:
        with get_db_session() as session:
            session_obj = session.get(ChatSession, session_id)
            if session_obj:
                session.delete(session_obj)
                session.commit()
                return True
        return False

    def close(self):
        pass