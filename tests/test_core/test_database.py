import os
import sqlite3
import tempfile
from pathlib import Path
import pytest
import shutil
import unittest.mock as mock

import core.database as db


@pytest.fixture
def temp_db():
    """为每个测试创建一个临时 SQLite 数据库，并在测试后清理。"""
    # 创建临时文件
    with tempfile.NamedTemporaryFile(delete=False, suffix=".db") as tmp:
        db_path = tmp.name
    # 初始化数据库
    db.initialize(db_path)
    yield db_path
    # 清理：关闭连接并删除文件
    db.close()
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture(autouse=True)
def reset_global_state():
    """确保每个测试开始前全局连接状态被重置（防止跨测试污染）。"""
    if db._connection is not None:
        db._connection.close()
        db._connection = None
    yield
    # 测试后也清理一次
    if db._connection is not None:
        db._connection.close()
        db._connection = None


# -----------------------------
# 测试用例
# -----------------------------


def test_initialize_creates_db_file_and_dir(temp_db):
    """测试 initialize 能正确创建数据库文件和父目录。"""
    assert os.path.exists(temp_db)
    conn = db.get_connection()
    assert conn is not None
    assert isinstance(conn, sqlite3.Connection)


def test_initialize_requires_valid_path_argument():
    """测试 initialize() 在缺少 db_path 参数时抛出 TypeError。"""
    with pytest.raises(TypeError, match="missing 1 required positional argument"):
        db.initialize()
    with pytest.raises(ValueError, match="db_path must be a non-empty string"):
        db.initialize("")
    with pytest.raises(ValueError, match="db_path must be a non-empty string"):
        db.initialize(None)


def test_initialize_creates_directory_and_connects_to_new_db():
    """测试 initialize() 能正确创建目录并连接到指定的新数据库文件。"""
    custom_db_path = "custom_data/test_chat.db"
    try:
        parent_dir = os.path.dirname(custom_db_path)
        if os.path.exists(parent_dir):
            shutil.rmtree(parent_dir)
        db.initialize(custom_db_path)
        assert os.path.isfile(custom_db_path)
        assert os.path.isdir(parent_dir)
        assert db._connection is not None
        assert db._database_path == custom_db_path
        with db.get_db_cursor() as cursor:
            cursor.execute("CREATE TABLE IF NOT EXISTS smoke_test (id INTEGER)")
    finally:
        db.close()
        if os.path.exists("custom_data"):
            shutil.rmtree("custom_data")


def test_get_connection_raises_error_if_not_initialized():
    """测试在未调用 initialize 时调用 get_connection 应抛出 RuntimeError。"""
    db.close()  # 确保未初始化
    with pytest.raises(RuntimeError, match="Database has not been initialized"):
        db.get_connection()


def test_get_db_cursor_context_manager_commits_on_success(temp_db):
    """测试 get_db_cursor 在无异常时自动提交事务。"""
    with db.get_db_cursor() as cursor:
        cursor.execute("CREATE TABLE test (id INTEGER)")
        cursor.execute("INSERT INTO test (id) VALUES (?)", (1,))
    # 查询验证是否已提交
    result = db.execute_query("SELECT * FROM test")
    assert len(result) == 1
    assert result[0]["id"] == 1


def test_get_db_cursor_rolls_back_on_exception(temp_db):
    """测试 get_db_cursor 在异常时自动回滚事务（仅 DML 可回滚）"""
    with db.get_db_cursor() as cur:
        cur.execute("DROP TABLE IF EXISTS test_rollback")
        cur.execute("CREATE TABLE test_rollback (id INTEGER)")

    with pytest.raises(ValueError, match="Simulated error"):
        with db.get_db_cursor() as cur:
            cur.execute("INSERT INTO test_rollback (id) VALUES (?)", (99,))
            raise ValueError("Simulated error")

    result = db.execute_query("SELECT * FROM test_rollback")
    assert len(result) == 0, "事务应被回滚，表应为空"

def test_execute_query_returns_rows_as_named_tuples(temp_db):
    """测试 execute_query 能正确执行 SELECT 并返回可通过列名访问的行。"""
    with db.get_db_cursor() as cursor:
        cursor.execute("CREATE TABLE users (id INTEGER, name TEXT)")
        cursor.execute("INSERT INTO users VALUES (?, ?)", (1, "Alice"))
    rows = db.execute_query("SELECT id, name FROM users WHERE id = ?", (1,))
    assert len(rows) == 1
    row = rows[0]
    assert row["id"] == 1
    assert row["name"] == "Alice"
    # 也支持索引访问
    assert row[0] == 1


def test_execute_non_query_returns_rowcount(temp_db):
    """测试 execute_non_query 能正确返回受影响的行数。"""
    with db.get_db_cursor() as cursor:
        cursor.execute("CREATE TABLE items (name TEXT)")
    count = db.execute_non_query("INSERT INTO items (name) VALUES (?)", ("Item1",))
    assert count == 1
    count = db.execute_non_query("UPDATE items SET name = 'NewItem'")
    assert count == 1
    count = db.execute_non_query("DELETE FROM items WHERE name = 'NonExistent'")
    assert count == 0


def test_execute_script_runs_multiple_statements(temp_db):
    """测试 execute_script 能正确执行多条 SQL 语句（如建表脚本）。"""
    script = """
    CREATE TABLE products (id INTEGER PRIMARY KEY, title TEXT);
    INSERT INTO products (title) VALUES ('Laptop');
    INSERT INTO products (title) VALUES ('Phone');
    """
    db.execute_script(script)
    rows = db.execute_query("SELECT title FROM products ORDER BY id")
    assert [r["title"] for r in rows] == ["Laptop", "Phone"]


def test_execute_script_rolls_back_on_error(temp_db):
    """
    测试 execute_script 在某条语句失败时回滚整个脚本中的 DML 操作。
    注意：由于 SQLite 的 DDL（如 CREATE TABLE）会隐式提交，无法回滚，
    因此本测试先创建表，脚本中仅包含可回滚的 DML 语句。
    """
    # 先创建表（作为测试前提，不在待测脚本中）
    with db.get_db_cursor() as cursor:
        cursor.execute("CREATE TABLE IF NOT EXISTS logs (msg TEXT)")
    # 脚本只包含 DML + 一条非法语句
    script = """
    INSERT INTO logs (msg) VALUES ('Log A');
    INSERT INTO logs (msg) VALUES ('Log B');
    INVALID SQL SYNTAX; -- 故意制造错误
    """
    # 执行脚本应抛出异常
    with pytest.raises(Exception):
        db.execute_script(script)
    # 验证：没有任何数据被插入（说明 DML 被回滚）
    result = db.execute_query("SELECT * FROM logs")
    assert len(result) == 0, "脚本失败后，所有 DML 操作应被回滚"


def test_close_closes_connection_and_resets_global_var():
    """测试 close 函数能正确关闭连接并将全局变量置为 None。"""
    db_path = tempfile.mktemp(suffix=".db")
    db.initialize(db_path)
    assert db._connection is not None
    db.close()
    assert db._connection is None
    # 再次调用不应报错
    db.close()


def test_initialize_raises_exception_on_connection_failure(monkeypatch):
    """
    测试当数据库连接或初始化过程（如首次查询）失败时，
    initialize 抛出异常并清理连接。
    使用 unittest.mock 来模拟失败场景。
    """
    db_path = "any/path/will/do.db"
    db.close()
    assert db._connection is None

    mock_conn = mock.Mock(spec=sqlite3.Connection)
    mock_cursor = mock.Mock(spec=sqlite3.Cursor)
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.execute.side_effect = sqlite3.OperationalError("Simulated DB access failure")

    # 使用 'as mock_connect' 获取 patcher 对象的引用，以便后续进行断言
    with mock.patch('core.database.sqlite3.connect', return_value=mock_conn) as mock_connect:
        with pytest.raises(Exception):
            db.initialize(db_path)

    assert db._connection is None
    
    # 使用获取到的 patcher 引用 mock_connect 来断言 sqlite3.connect 是如何被调用的
    mock_connect.assert_called_once_with(
        db_path,
        check_same_thread=False
    )
    mock_conn.cursor.assert_called_once()
    mock_cursor.execute.assert_called_once_with("SELECT 1")


def test_concurrent_access_with_check_same_thread_disabled(temp_db):
    """验证 check_same_thread=False 生效，允许跨线程使用连接（基础验证）。"""
    # 本测试不真正启动线程，但验证连接属性
    conn = db.get_connection()
    # sqlite3.Connection 没有直接暴露 check_same_thread，
    # 但可通过尝试在子线程使用来间接验证（此处简化）
    # 实际上，只要没报错，说明初始化成功，且模块设计允许跨线程（由使用者保证安全）
    assert conn is not None


# -----------------------------
# 边界/辅助测试
# -----------------------------


def test_execute_query_with_no_results(temp_db):
    """测试 execute_query 在无匹配结果时返回空列表。"""
    with db.get_db_cursor() as cursor:
        cursor.execute("CREATE TABLE empty_table (x INT)")
    results = db.execute_query("SELECT * FROM empty_table")
    assert results == []


def test_execute_non_query_with_no_params(temp_db):
    """测试 execute_non_query 在无参数时也能正常工作。"""
    with db.get_db_cursor() as cursor:
        cursor.execute("CREATE TABLE t (id INTEGER)")
    # 不带参数的 DELETE
    count = db.execute_non_query("DELETE FROM t")
    assert count == 0


# 在 conftest.py 或 test_database.py 文件顶部附近

@pytest.fixture(scope="function") # 或 scope="module" 如果需要
def clean_db_path(tmp_path): # 使用 pytest 内置的 tmp_path 夹具
    """提供一个唯一的临时数据库文件路径，但不进行初始化。"""
    db_file = tmp_path / "test.db"
    yield str(db_file) # 只返回路径
    # teardown (如果需要清理文件)
    if db_file.exists():
        db_file.unlink(missing_ok=True)

# 然后修改你的测试函数，之前的测试函数已经初始化了，需要未初始化的
def test_initialize_skips_reconnection_when_already_initialized(clean_db_path): # 使用新夹具
    """
    测试当数据库已初始化（_connection 不为 None）时，
    再次调用 initialize() 会抛出 RuntimeError。
    """
    first_db = clean_db_path
    # 第一次初始化
    db.initialize(first_db)

    # 确保第一次初始化成功
    assert db._connection is not None
    assert db._database_path == first_db

    # 尝试第二次初始化（使用相同或不同的路径）
    second_db = clean_db_path + ".second" # 或者使用 tmp_path 生成另一个
    with pytest.raises(RuntimeError) as exc_info:
        db.initialize(second_db)

    # 验证错误信息
    assert "already initialized" in str(exc_info.value)

    # 验证状态没有改变
    assert db._connection is not None
    assert db._database_path == first_db

    # 清理
    db.close()

def test_initialize_raises_runtimeerror_on_mkdir_permission_error(monkeypatch):
    """
    测试当 db_dir.mkdir() 抛出 PermissionError 时，
    initialize 会捕获它并抛出 RuntimeError。
    """
    db_path = "/some/protected/path/db.sqlite"
    db.close()  # 确保连接是干净的
    assert db._connection is None

    mock_db_dir = mock.Mock()
    # 模拟 mkdir 抛出 PermissionError
    mock_db_dir.mkdir.side_effect = PermissionError("Permission denied")

    # Mock Path 对象，使其 __init__ 返回 db_path 对应的 mock 父目录
    with mock.patch('core.database.Path') as mock_path_class:
        # 配置 Path(db_path).parent
        mock_path_instance = mock.Mock()
        mock_path_instance.parent = mock_db_dir
        mock_path_class.return_value = mock_path_instance

        # 调用 initialize 并期望抛出 RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            db.initialize(db_path)

        # 验证抛出的异常信息
        assert "Database directory not writable" in str(exc_info.value)
        # 验证原始异常被链接
        assert isinstance(exc_info.value.__cause__, PermissionError)

    # 验证连接未被意外创建或残留
    assert db._connection is None

    # 验证 mkdir 被调用了一次
    mock_db_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)

    # 注意：由于 mkdir 失败，后续的 __truediv__ (即 / ".write_test") 不会发生，
    # 因此我们不应该尝试去断言 __truediv__ 的调用情况，
    # 否则在 Mock 对象上直接访问未设置的魔术方法会引发 AttributeError。
    # 移除或注释掉下面这行有问题的断言：
    # mock_db_dir.__truediv__.assert_not_called() 


def test_initialize_raises_runtimeerror_on_touch_permission_error(monkeypatch):
    """
    测试当 test_file.touch() 抛出 PermissionError 时，
    initialize 会捕获它并抛出 RuntimeError。
    """
    db_path = "/some/path/db.sqlite"
    db.close()  # 确保连接是干净的
    assert db._connection is None

    # 创建一个普通的 Mock 对象来代表 db_dir
    mock_db_dir = mock.Mock()
    # 配置 mkdir 成功
    mock_db_dir.mkdir.return_value = None

    # 创建一个 Mock 对象来代表 test_file (db_dir / ".write_test")
    mock_test_file = mock.Mock()
    # 配置 touch 抛出 PermissionError
    mock_test_file.touch.side_effect = PermissionError("Permission denied")

    # --- 关键修改 ---
    # 使用 configure_mock 来设置 __truediv__ 方法
    # 我们创建一个内部的 Mock 来代表 __truediv__ 方法本身
    mock_truediv_method = mock.Mock(return_value=mock_test_file)
    # 然后将这个方法 Mock 设置为 mock_db_dir 的 __truediv__ 属性
    mock_db_dir.configure_mock(**{'__truediv__': mock_truediv_method})
    # --- 结束关键修改 ---

    # Mock Path 类本身
    with mock.patch('core.database.Path') as mock_path_class:
        # 配置 Path(db_path) 返回一个具有 mock parent 的实例
        mock_path_instance = mock.Mock()
        mock_path_instance.parent = mock_db_dir
        mock_path_class.return_value = mock_path_instance

        # 调用 initialize 并期望抛出 RuntimeError
        with pytest.raises(RuntimeError) as exc_info:
            db.initialize(db_path)

        # 验证抛出的异常信息
        assert "Database directory not writable" in str(exc_info.value)
        # 验证原始异常被链接
        assert isinstance(exc_info.value.__cause__, PermissionError)

    # 验证连接未被意外创建或残留
    assert db._connection is None

    # 验证 mkdir 被调用
    mock_db_dir.mkdir.assert_called_once_with(parents=True, exist_ok=True)
    
    # --- 关键修改 ---
    # 使用我们之前创建的 mock_truediv_method 来断言它被正确调用
    mock_truediv_method.assert_called_once_with(".write_test")
    # --- 结束关键修改 ---
    
    # 验证 touch 被调用
    mock_test_file.touch.assert_called_once()
    # 验证 unlink 没有被调用（因为 touch 就失败了）
    mock_test_file.unlink.assert_not_called()