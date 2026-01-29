# backend/core/services/chat_service.py

import os
from typing import List, Optional, Generator
from datetime import datetime
from sqlalchemy import desc

from langchain_core.messages import HumanMessage, AIMessage
from langchain_openai import ChatOpenAI
# from langchain_anthropic import ChatAnthropic
from langchain_ollama import ChatOllama

from shared.chat_schemas import ChatTurnResponse
from backend.db_models.chat_models import LLMConfig, ChatSession, ChatMessage
from backend.services.llm_setting_service import LLMSettingService 
from backend.core.database import get_session



class ChatService:
    """
    聊天服务：支持完整响应与流式输出。
    所有状态从数据库读取，服务本身无状态。
    """

    def __init__(self):
        self._session = next(get_session())

    def _get_llm_client(self, config: LLMConfig):
        """根据配置创建 LangChain LLM 客户端"""
        api_key = os.getenv(config.api_key_name)
        if not api_key:
            raise ValueError(f"环境变量 {config.api_key_name} 未设置")

        provider = config.provider.lower()
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
        elif provider == "ollama":
            return ChatOllama(
                model=config.model_name,
                base_url=config.base_url or "http://localhost:11434",
                temperature=0.7,
            )
        else:
            raise ValueError(f"不支持的 LLM 提供商: {config.provider}")

    def create_session(self, title: str, config_id: int) -> ChatSession:
        session = ChatSession(title=title, config_id=config_id)
        self._session.add(session)
        self._session.commit()
        self._session.refresh(session)
        return session

    def get_session(self, session_id: int) -> Optional[ChatSession]:
        return self._session.get(ChatSession, session_id)

    def list_sessions(self) -> List[ChatSession]:
        """获取所有聊天会话，按更新时间倒序排列"""
        return self._session.query(ChatSession).order_by(desc(ChatSession.updated_at)).all()

    def get_session_messages(self, session_id: int) -> List[ChatMessage]:
        return (
            self._session.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at)
            .all()
        )

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
        self._session.add(message)
        self._session.commit()
        self._session.refresh(message)
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
    def chat_turn(self, session_id: int, user_message: str) -> ChatTurnResponse:
        session = self.get_session(session_id)
        if not session:
            raise ValueError(f"会话 ID {session_id} 不存在")
        
        config = LLMSettingService().get_active()  # ← 直接获取全局配置
        
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
        session.updated_at = datetime.utcnow()
        self._session.add(session)
        self._session.commit()

        return ChatTurnResponse(
            session_id=session_id,
            user_message=user_message,
            assistant_reply=assistant_reply,
            message_id=assistant_msg.id,
        )

    # ======================
    # 流式：生成器
    # 注意：此方法不保存消息！由调用方在流结束后处理
    # ======================
    def chat_turn_stream(self, session_id: int, user_message: str) -> Generator[str, None, None]:
        session = self.get_session(session_id)
        if not session:
            yield "[ERROR: 会话不存在]"
            return
        config = session.config
        if not config:
            yield "[ERROR: LLM 配置丢失]"
            return

        history = self._build_history(session_id, user_message)
        llm = self._get_llm_client(config)

        try:
            for chunk in llm.stream(history):
                token = chunk.content
                if token:
                    yield token
        except Exception as e:
            yield f"[ERROR: {str(e)}]"

    def delete_session(self, session_id: int) -> bool:
        session = self.get_session(session_id)
        if session:
            self._session.delete(session)
            self._session.commit()
            return True
        return False

    def close(self):
        self._session.close()