# core/database.py

"""
SQLite 数据库管理模块。
提供数据库连接初始化、基础 CRUD 操作的便捷接口以及上下文管理器。

此模块旨在提供一个轻量级、可复用的数据库访问层，方便上层服务（如 services/*_service.py）使用。
"""

import sqlite3
import os
import logging
from contextlib import contextmanager
from typing import Generator, List, Any

# --- 模块级变量 ---
_connection = None
_database_path = None
_logger = logging.getLogger(__name__)


def initialize(db_path: str = "data/chat_history.db"):
    """
    初始化数据库连接并创建必要的表。

    Args:
        db_path (str): SQLite 数据库文件的路径。默认为 "data/chat_history.db"。

    Raises:
        Exception: 如果初始化过程中发生错误。
    """
    global _connection, _database_path
    _database_path = db_path

    # 确保 data 目录存在
    os.makedirs(os.path.dirname(_database_path), exist_ok=True)

    try:
        if _connection is None:
            # check_same_thread=False 允许跨线程使用连接，但使用者需保证线程安全
            _connection = sqlite3.connect(
                _database_path, check_same_thread=False)
            _connection.row_factory = sqlite3.Row  # 使得查询结果可以通过列名访问
            _logger.info(f"Connected to SQLite database at {_database_path}")

        # --- 在此处放置创建表的 SQL 脚本 ---
        # 示例：创建一个示例表。实际表应在对应 service 初始化时创建。
        # 例如，在 services/chat_history_service.py 的初始化方法中调用 execute_script
        # 来创建 chat_history 表。
        # create_example_table_sql = """
        # CREATE TABLE IF NOT EXISTS example_items (
        #     id INTEGER PRIMARY KEY AUTOINCREMENT,
        #     name TEXT NOT NULL,
        #     description TEXT,
        #     created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        # );
        # """
        # execute_script(create_example_table_sql)
        # ---------------------------------------

        _logger.info(
            "Database initialization completed (table creation logic should be in services).")

    except Exception as e:
        _logger.error(f"Failed to initialize database: {e}")
        # 初始化失败时清理连接
        if _connection:
            _connection.close()
            _connection = None
        raise e


def get_connection():
    """
    获取数据库连接实例。

    Returns:
        sqlite3.Connection: 数据库连接对象。

    Raises:
        RuntimeError: 如果数据库未初始化。
    """
    if _connection is None:
        raise RuntimeError(
            "Database has not been initialized. Call initialize() first.")
    return _connection


@contextmanager
def get_db_cursor() -> Generator[sqlite3.Cursor, None, None]:
    """
    上下文管理器，提供一个数据库游标，并自动处理事务提交/回滚和游标关闭。
    这是执行数据库操作的推荐方式。

    Yields:
        sqlite3.Cursor: 数据库游标对象。

    Example:
        >>> from core.database import get_db_cursor
        >>> with get_db_cursor() as cursor:
        ...     cursor.execute("INSERT INTO items (name) VALUES (?)", ("Test Item",))
        ...     # 事务会在退出 with 块时自动 commit
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        yield cursor
        conn.commit()
    except Exception as e:
        conn.rollback()
        _logger.error(
            f"Database transaction rolled back due to: {e}", exc_info=True)
        raise e
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


def execute_script(script: str):
    """
    执行多条 SQL 语句脚本 (例如，创建表的 DDL 脚本)。

    Args:
        script (str): 包含多条 SQL 语句的脚本字符串。

    Raises:
        Exception: 如果脚本执行失败。
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.executescript(script)
        conn.commit()
    except Exception as e:
        conn.rollback()
        _logger.error(
            f"SQL script execution failed and was rolled back: {e}",
            exc_info=True)
        raise e
    finally:
        cursor.close()


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
