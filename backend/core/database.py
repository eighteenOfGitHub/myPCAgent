# backend/core/database.py

import os
from pathlib import Path

from contextlib import contextmanager
from sqlmodel import inspect
from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy.engine import Engine

from ..core.config.back_config import back_config

# ----------------------------
# 数据库配置
# ----------------------------

# 确保 data 目录存在
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / back_config.DATABASE.data_dir
DATA_DIR.mkdir(parents=True, exist_ok=True)

# SQLite 数据库路径
DB_PATH = DATA_DIR / back_config.DATABASE.db_filename
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DB_PATH}")

# SQLite 需要特殊参数
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}

# 创建引擎
engine: Engine = create_engine(DATABASE_URL, connect_args=connect_args, echo=False)


# ----------------------------
# 初始化数据库（创建表）
# ----------------------------

def init_db():
    """
    创建所有 SQLModel 表。
    在应用启动时调用一次。
    """
    # 导入所有模型（触发 SQLModel 元类注册）
    from backend.db_models.chat_models import ChatSession, ChatMessage
    from backend.db_models.user_config import LLMConfig, UserPreference



    # 获取数据库中已存在的表名列表
    existing_tables = inspect(engine).get_table_names()
    if existing_tables:
        print(f"📊 已存在的表: {existing_tables}")
    else:
        print("📊 已存在的表: []")
        
    SQLModel.metadata.create_all(engine)


# ----------------------------
# 会话管理
# ----------------------------

def get_session():
    """
    FastAPI 依赖项使用的 DB 会话生成器。
    支持 with 或 for 自动关闭。
    """
    with Session(engine) as session:
        yield session


# 新增：上下文管理器
@contextmanager
def get_db_session():
    """提供一个数据库会话的上下文管理器，确保会话在使用后被正确关闭。"""
    session_gen = get_session()
    session = next(session_gen)
    try:
        yield session
    except Exception:
        session.rollback() # 如果发生异常，回滚事务
        raise # 重新抛出异常
    finally:
        next(session_gen, None) # 触发生成器的 finally 块以关闭 session        