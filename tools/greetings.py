# utils/greetings.py

def get_pca_greeting() -> str:
    """
    返回 PC Agent 的默认问候语。
    
    Returns:
        str: 固定的问候语字符串。
    """
    return "Hello! I'm your exclusive PCAgent, can I help you?"

# 如果将来需要更复杂的服务逻辑，可以创建服务层文件
# services/pca_service.py
# from utils.greetings import get_pca_greeting
#
# class PCAgentService:
#     def __init__(self):
#         pass
#
#     def say_hello(self) -> str:
#         # 可以在这里添加业务逻辑，例如记录日志、获取用户信息等
#         greeting = get_pca_greeting()
#         # ... 其他业务处理 ...
#         return greeting