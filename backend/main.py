"""
backend/main.py

FastAPI 应用的主入口点。

此模块创建 FastAPI 应用实例，包含 API 路由，并提供启动函数。
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.api.v1.router import router
from backend.config.back_config import back_config

# --- FastAPI 应用实例 ---
app = FastAPI(title=" Backend API",)

# --- 中间件配置 ---
# 允许跨域请求，方便前端 Gradio 应用访问
app.add_middleware(
    CORSMiddleware,
    allow_origins=back_config.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- 包含 API 路由 ---
# 将定义在 api_router 中的所有路由注册到 app
app.include_router(router, prefix="/api/v1")

# --- 根路径健康检查 ---
@app.get("/")
def read_root():
    """
    根路径健康检查端点。

    Returns:
        dict: 返回一个简单的欢迎信息。
    """
    return {"message": "LangGraph Backend API is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host=back_config.BACKEND_HOST,
        port=back_config.BACKEND_PORT,
        reload=back_config.BACKEND_RELOAD,
        reload_dirs=[".", "../config", "../shared"]
    )


    