"""backend/main.py
FastAPI 应用的主入口点。此模块创建 FastAPI 应用实例，包含 API 路由，并提供启动函数。
"""
import sys
from pathlib import Path

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

import logging
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.api.router import router
from backend.core.config.back_config import back_config
from backend.core.database import init_db
from backend.core import logger  # 导入 logger 模块
from backend.middleware.logging_middleware import LoggingMiddleware # 导入中间件

# --- 日志系统初始化 (移到最前面) ---
logger.setup_logging()
# 获取 logger 实例用于 main.py 的日志记录
main_logger = logging.getLogger(__name__) # 或者使用 logging.getLogger("backend.main")
main_logger.info("Backend application starting up...")

try:
    init_db()
    main_logger.info("✅ 数据库初始化成功：表已创建或已存在")
except Exception as e:
    main_logger.error(f"❌ 数据库初始化失败: {e}", exc_info=True) # 使用 exc_info=True 记录堆栈
    raise

# --- FastAPI 应用实例 ---
app = FastAPI(title=" Backend API",)

# --- 中间件配置 ---
# 注意：日志中间件通常放在最外层（最先注册），以便捕获所有请求
app.add_middleware(LoggingMiddleware) # 添加日志中间件

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
app.include_router(router, prefix="/api")

if __name__ == "__main__":
    import uvicorn
    main_logger.info(f"Starting Uvicorn server on {back_config.BACKEND_HOST}:{back_config.BACKEND_PORT}")
    uvicorn.run(
        app,
        host=back_config.BACKEND_HOST,
        port=back_config.BACKEND_PORT,
        log_level="error"
    )