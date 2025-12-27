# core/database.py
"""SQLite 数据库访问模块。提供一个 SQLiteDatabase 类来管理连接和执行操作。"""

import sqlite3
from contextlib import contextmanager, closing
from typing import Generator, Optional, List
from core.logger import get_logger
from pathlib import Path


class SQLiteDatabase:
    """
    SQLite 数据库访问类。
    
    注意：为保证线程安全，每次数据库操作都会创建新连接。
    对于需要多语句事务的场景，请使用 `get_db_cursor()` 上下文管理器。
    """

    def __init__(self, db_path: str):
        """
        初始化 SQLite 数据库实例。
        Args:
            db_path (str): SQLite 数据库文件路径。
        """
        if not db_path:
            raise ValueError("db_path must be a non-empty string")
        
        self.db_path = db_path
        self.logger = get_logger(__name__)
        
        # 确保数据库目录可写（保留你的原逻辑）
        db_dir = Path(self.db_path).parent
        try:
            db_dir.mkdir(parents=True, exist_ok=True)
            test_file = db_dir / ".write_test"
            test_file.touch()
            test_file.unlink()
        except (OSError, PermissionError) as e:
            self.logger.error(f"Cannot write to database directory {db_dir}: {e}")
            raise RuntimeError(f"Database directory not writable: {db_dir}") from e

    def _create_connection(self) -> sqlite3.Connection:
        """创建并配置新的数据库连接"""
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=True,  # ← 关键：启用线程检查（更安全）
            isolation_level=None     # ← 自动提交关闭，由我们控制事务
        )
        conn.row_factory = sqlite3.Row
        return conn

    @contextmanager
    def get_db_cursor(self) -> Generator[sqlite3.Cursor, None, None]:
        """
        上下文管理器，提供数据库游标，并自动处理事务提交/回滚和连接关闭。
        
        使用示例：
            with db.get_db_cursor() as cursor:
                cursor.execute("INSERT INTO ...")
                cursor.execute("UPDATE ...")
        """
        conn = None
        cursor = None
        try:
            conn = self._create_connection()
            cursor = conn.cursor()
            # 显式开启事务
            cursor.execute("BEGIN")
            yield cursor
            conn.commit()
            self.logger.debug("Transaction committed successfully.")
        except Exception as e:
            if conn:
                conn.rollback()
            self.logger.error(f"Database transaction rolled back due to: {e}", exc_info=True)
            raise
        finally:
            if cursor:
                cursor.close()
            if conn:
                conn.close()

    def execute_query(self, query: str, params: tuple = ()) -> List[sqlite3.Row]:
        """
        执行 SELECT 查询并返回所有结果。
        每次调用创建新连接，线程安全。
        """
        with self._create_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute(query, params)
            result = cursor.fetchall()
            cursor.close()
            return result

    def execute_non_query(self, query: str, params: tuple = ()) -> int:
        """
        执行 INSERT, UPDATE, DELETE 等非查询操作。
        每次调用创建新连接，自动提交，线程安全。
        """
        with self._create_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rowcount = cursor.rowcount
            cursor.close()
            conn.commit()  # 显式提交
            return rowcount

    def execute_script(self, sql_script: str) -> None:
        """
        执行多条 SQL 语句（DML），并在出错时回滚所有操作。
        使用单个连接保证原子性。
        """
        with self._create_connection() as conn:
            try:
                conn.execute("BEGIN")
                conn.executescript(sql_script)
                conn.commit()
                self.logger.info("SQL script executed successfully.")
            except Exception as e:
                conn.rollback()
                self.logger.error(f"Script execution failed, rolled back: {e}")
                raise

    def close(self):
        """
        兼容性方法：当前实现无需关闭（无持久连接），
        但保留以避免调用方报错。
        """
        self.logger.info("🏁 SQLiteDatabase has no persistent connection to close.")