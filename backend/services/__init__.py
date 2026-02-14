from typing import Optional

_chat_service = None
_llm_setting_service = None
_default_setting_service = None

def get_chat_service():
    global _chat_service
    if _chat_service is None:
        from backend.services.chat_service import ChatService
        _chat_service = ChatService()
    return _chat_service

def get_llm_setting_service():
    global _llm_setting_service
    if _llm_setting_service is None:
        from backend.services.llm_setting_service import LLMSettingService
        _llm_setting_service = LLMSettingService()
    return _llm_setting_service

def get_default_setting_service():
    global _default_setting_service
    if _default_setting_service is None:
        from backend.services.default_setting_service import DefaultSettingService
        _default_setting_service = DefaultSettingService()
    return _default_setting_service
