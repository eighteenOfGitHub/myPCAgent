# backend/core/database.py

from sqlmodel import create_engine, Session, SQLModel
from sqlalchemy.engine import Engine
import os
from pathlib import Path

# ----------------------------
# 数据库配置
# ----------------------------

# 确保 data 目录存在
DATA_DIR = Path(__file__).parent.parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)

# SQLite 数据库路径
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{DATA_DIR}/pcagent.db")

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
    from backend.db_models.chat_models import LLMConfig, ChatSession, ChatMessage

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