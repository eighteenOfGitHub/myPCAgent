from fastapi import APIRouter

from tools.greetings import get_pca_greeting


# Router for greeting-related endpoints
router = APIRouter(
    prefix="/greetings",
    tags=["Greetings"],
)


@router.get("/sayhello", summary="获取 PC Agent 问候语")
async def say_hello_endpoint():
    """
    调用工具函数获取问候语并返回。
    """
    message = get_pca_greeting()
    return {"message": message}