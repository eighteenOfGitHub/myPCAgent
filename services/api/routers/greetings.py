# api/routers/greetings_api.py

from fastapi import APIRouter
# 从工具层导入函数
from tools.greetings import get_pca_greeting

# 创建 APIRouter 实例
# prefix: 为此模块下所有路由添加统一前缀，例如 /greetings/sayhello
# tags: 在 API 文档中将这些路由归类到 "Greetings" 标签下
router = APIRouter(
    prefix="/greetings",
    tags=["Greetings"]
)

# 定义具体的 API 端点
# 访问此端点的实际 URL 将是: {base_url}/greetings/sayhello
@router.get("/sayhello", summary="获取 PC Agent 问候语")
async def say_hello_endpoint():
    """
    调用工具函数获取问候语并返回。
    """
    # 调用工具层的函数
    message = get_pca_greeting()
    # FastAPI 会自动将 dict 序列化为 JSON 响应
    return {"message": message}

# 你可以在此文件中添加更多与 greetings 相关的 API 端点
# 例如 POST /greetings/customize 来设置个性化问候语等