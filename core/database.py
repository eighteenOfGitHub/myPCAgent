# core/database.py
import sqlite3
from contextlib import contextmanager
from typing import Generator, Optional
import logging
from pathlib import Path
from typing import List

_logger = logging.getLogger(__name__)

_connection = None
_database_path = None

def initialize(db_path: str) -> None:
    """初始化 SQLite 数据库连接。"""
    global _connection, _database_path

    if not db_path:
        raise ValueError("db_path must be a non-empty string")

    if _connection is not None:
        raise RuntimeError("Database already initialized. Call close() first if reinitializing.")

    _database_path = db_path
    db_dir = Path(_database_path).parent

    try:
        db_dir.mkdir(parents=True, exist_ok=True)
        # --- 添加写权限测试 ---
        test_file = db_dir / ".write_test"
        test_file.touch()
        test_file.unlink()
        # ---------------------
    except (OSError, PermissionError) as e:
        _logger.error(f"Cannot write to database directory {db_dir}: {e}")
        raise RuntimeError(f"Database directory not writable: {db_dir}") from e

    try:
        # 连接数据库
        conn = sqlite3.connect(
            _database_path,
            check_same_thread=False
        )
        conn.row_factory = sqlite3.Row
        _connection = conn
        
        # ---- 关键修改：主动执行一个 SQL 操作 ----
        # 这会强制 SQLite 尝试创建/打开文件，从而暴露路径或权限问题
        cursor = conn.cursor()
        cursor.execute("SELECT 1") # 一个轻量且无害的查询
        cursor.close()
        # -----------------------------------------
        
        _logger.info(f"Connected to SQLite database at {_database_path}")
        _logger.info("Database initialization completed.")
    except Exception as e: # 捕获所有连接或初始查询相关的异常
        _logger.error(f"Failed to connect to SQLite database at {_database_path}: {e}")
        # 确保在初始化失败时清理连接
        if _connection:
            _connection.close()
            _connection = None
        raise # 重新抛出异常，让调用者知道初始化失败了


def get_connection():
    """获取当前数据库连接。"""
    if _connection is None:
        raise RuntimeError("Database has not been initialized")
    return _connection


@contextmanager
def get_db_cursor() -> Generator[sqlite3.Cursor, None, None]:
    """上下文管理器，提供数据库游标，并自动处理事务提交/回滚和游标关闭。"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        # 👇 显式开启事务
        cursor.execute("BEGIN")
        yield cursor
        conn.commit()
        _logger.debug("Transaction committed successfully.")
    except Exception as e:
        conn.rollback()
        _logger.error(f"Database transaction rolled back due to: {e}", exc_info=True)
        raise
    finally:
        cursor.close()


def execute_query(query: str, params: tuple = ()) -> List[sqlite3.Row]:
    """
    执行 SELECT 查询并返回所有结果。

    Args:
        query (str): SQL SELECT 查询语句。
        params (tuple): 查询参数。默认为空元组。

    Returns:
        list[sqlite3.Row]: 查询结果列表。每行是一个 sqlite3.Row 对象，可通过索引或列名访问。
    """
    with get_db_cursor() as cursor:
        cursor.execute(query, params)
        return cursor.fetchall()


def execute_non_query(query: str, params: tuple = ()) -> int:
    """
    执行 INSERT, UPDATE, DELETE 等非查询操作。
    注意：此函数会触发自动 commit。对于复杂的事务操作，建议直接使用 `get_db_cursor()` 上下文管理器。

    Args:
        query (str): SQL 非查询语句。
        params (tuple): 查询参数。默认为空元组。

    Returns:
        int: 受影响的行数。
    """
    # 内部使用 get_db_cursor 确保自动 commit/rollback
    with get_db_cursor() as cursor:
        cursor.execute(query, params)
        return cursor.rowcount


def execute_script(sql_script: str) -> None:
    """
    执行多条 SQL 语句（支持 DML），并在出错时回滚所有操作。
    
    注意：不支持 DDL（如 CREATE TABLE），因为 SQLite DDL 会隐式提交。
    建议仅用于 INSERT/UPDATE/DELETE 等 DML 脚本。
    """
    conn = get_connection()
    # 分割 SQL 脚本为单条语句（简单按 ';' 分割，适用于大多数场景）
    statements = [
        stmt.strip() 
        for stmt in sql_script.split(';') 
        if stmt.strip()
    ]
    
    try:
        # 显式开始事务（禁用 autocommit）
        conn.execute("BEGIN")
        for stmt in statements:
            conn.execute(stmt)
        conn.commit()
    except Exception as e:
        conn.rollback()
        _logger.error(f"Script execution failed, rolled back: {e}")
        raise


def close():
    """
    关闭数据库连接。
    """
    global _connection
    if _connection:
        _connection.close()
        _connection = None
        _logger.info("Database connection closed.")

# --- 使用示例 (应在 services/*_service.py 中) ---
#
# from core.database import get_db_cursor, execute_query, execute_script
#
# class ChatHistoryService:
#
#     def initialize_table(self):
#         schema_sql = """
#             CREATE TABLE IF NOT EXISTS chat_history (
#                 id INTEGER PRIMARY KEY AUTOINCREMENT,
#                 session_id TEXT NOT NULL,
#                 role TEXT NOT NULL CHECK(role IN ('user', 'assistant')),
#                 content TEXT NOT NULL,
#                 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
#             );
#         """
#         execute_script(schema_sql)
#         # 或者在 database.initialize() 中预留钩子调用此类方法
#
#     def add_message(self, session_id: str, role: str, content: str):
#         sql = "INSERT INTO chat_history (session_id, role, content) VALUES (?, ?, ?)"
#         # 推荐使用上下文管理器控制事务
#         with get_db_cursor() as cursor:
#             cursor.execute(sql, (session_id, role, content))
#         # 或者使用 execute_non_query (它内部也是使用的上下文管理器)
#         # execute_non_query(sql, (session_id, role, content))
#
#     def get_history(self, session_id: str) -> List[sqlite3.Row]:
#         sql = "SELECT * FROM chat_history WHERE session_id = ? ORDER BY timestamp ASC"
#         return execute_query(sql, (session_id,))
#
