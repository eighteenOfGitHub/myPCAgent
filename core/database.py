# core/database.py
"""SQLite 数据库访问模块。提供一个 SQLiteDatabase 类来管理连接和执行操作。"""

import sqlite3
from contextlib import contextmanager
from typing import Generator, Optional, List
import logging
from pathlib import Path


class SQLiteDatabase:
    """
    SQLite 数据库访问类。
    管理数据库连接，并提供执行查询和非查询操作的方法。
    Logger 在初始化时传入。
    """

    def __init__(self, db_path: str, logger: logging.Logger):
        """
        初始化 SQLite 数据库实例。

        Args:
            db_path (str): SQLite 数据库文件路径。
            logger (logging.Logger): 用于记录日志的 logger 实例。
        """
        self.db_path = db_path
        self.logger = logger
        self.connection: Optional[sqlite3.Connection] = None
        self._initialize_connection()

    def _initialize_connection(self):
        """初始化数据库连接。"""
        if not self.db_path:
            raise ValueError("db_path must be a non-empty string")

        db_dir = Path(self.db_path).parent
        try:
            db_dir.mkdir(parents=True, exist_ok=True)
            # --- 添加写权限测试 ---
            test_file = db_dir / ".write_test"
            test_file.touch()
            test_file.unlink()
            # ---------------------
        except (OSError, PermissionError) as e:
            self.logger.error(f"Cannot write to database directory {db_dir}: {e}")
            raise RuntimeError(f"Database directory not writable: {db_dir}") from e

        try:
            # 连接数据库
            conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False  # 允许多线程访问，但需小心使用
            )
            conn.row_factory = sqlite3.Row  # 使结果可以通过列名访问
            self.connection = conn

            # ---- 关键修改：主动执行一个 SQL 操作 ----
            # 这会强制 SQLite 尝试创建/打开文件，从而暴露路径或权限问题
            cursor = conn.cursor()
            cursor.execute("SELECT 1")  # 一个轻量且无害的查询
            cursor.close()
            # -----------------------------------------
            self.logger.info(f"Connected to SQLite database at {self.db_path}")
        except Exception as e:
            # 捕获所有连接或初始查询相关的异常
            self.logger.error(f"Failed to connect to SQLite database at {self.db_path}: {e}")
            # 确保在初始化失败时清理连接
            if self.connection:
                self.connection.close()
                self.connection = None
            raise  # 重新抛出异常，让调用者知道初始化失败了

    def get_connection(self) -> sqlite3.Connection:
        """获取当前数据库连接。"""
        if self.connection is None:
            raise RuntimeError("Database connection has not been established.")
        return self.connection

    @contextmanager
    def get_db_cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        """
        上下文管理器，提供数据库游标，并自动处理事务提交/回滚和游标关闭。
        使用实例的 self.logger 记录事务日志。
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        try:
            # 显式开启事务
            cursor.execute("BEGIN")
            yield cursor
            conn.commit()
            self.logger.debug("Transaction committed successfully.")
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Database transaction rolled back due to: {e}", exc_info=True)
            raise
        finally:
            cursor.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """
        执行 SELECT 查询并返回所有结果。

        Args:
            query (str): SQL SELECT 查询语句。
            params (tuple): 查询参数。默认为空元组。

        Returns:
            list[sqlite3.Row]: 查询结果列表。每行是一个 sqlite3.Row 对象。
        """
        with self.get_db_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.fetchall()

    def execute_non_query(self, query: str, params: tuple = ()) -> int:
        """
        执行 INSERT, UPDATE, DELETE 等非查询操作。
        注意：此函数会触发自动 commit。对于复杂的事务操作，建议直接使用 `get_db_cursor()`。

        Args:
            query (str): SQL 非查询语句。
            params (tuple): 查询参数。默认为空元组。

        Returns:
            int: 受影响的行数。
        """
        # 内部使用 get_db_cursor 确保自动 commit/rollback
        with self.get_db_cursor() as cursor:
            cursor.execute(query, params)
            return cursor.rowcount

    def execute_script(self, sql_script: str) -> None:
        """
        执行多条 SQL 语句（支持 DML），并在出错时回滚所有操作。
        注意：不支持 DDL（如 CREATE TABLE），因为 SQLite DDL 会隐式提交。
        建议仅用于 INSERT/UPDATE/DELETE 等 DML 脚本。

        Args:
            sql_script (str): 包含多条 SQL 语句的字符串。
        """
        conn = self.get_connection()
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
            self.logger.info("SQL script executed successfully.")
        except Exception as e:
            conn.rollback()
            self.logger.error(f"Script execution failed, rolled back: {e}")
            raise

    def close(self):
        """关闭数据库连接。"""
        if self.connection:
            self.connection.close()
            self.connection = None
            self.logger.info("🏁 Database connection closed.")