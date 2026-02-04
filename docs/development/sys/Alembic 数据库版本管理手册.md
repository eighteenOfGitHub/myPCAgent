# Alembic 数据库版本管理手册

## 📚 目录

1. 快速参考
2. 初始化设置
3. 日常开发流程
4. 常见场景操作
5. 迁移管理
6. 故障排查
7. 团队协作规范

---

## 快速参考

### 常用命令速查表

| 操作 | 命令 | 说明 |
|------|------|------|
| **初始化** | `alembic init migrations` | 初始化 Alembic |
| **生成迁移** | `alembic revision --autogenerate -m "描述"` | 自动检测变更并生成迁移 |
| **手动迁移** | `alembic revision -m "描述"` | 手动创建空白迁移脚本 |
| **升级到最新** | `alembic upgrade head` | 应用所有待执行的迁移 |
| **升级N步** | `alembic upgrade +1` | 向前执行1个迁移 |
| **回滚到版本** | `alembic downgrade <revision_id>` | 回滚到指定版本 |
| **回滚N步** | `alembic downgrade -1` | 回退1个版本 |
| **查看当前版本** | `alembic current` | 显示数据库当前版本 |
| **查看历史** | `alembic history` | 显示所有迁移历史 |
| **查看详细历史** | `alembic history --verbose` | 显示详细迁移信息 |
| **生成SQL预览** | `alembic upgrade head --sql` | 输出SQL而不执行 |
| **标记为已执行** | `alembic stamp head` | 标记版本（不执行SQL） |

---

## 初始化设置

### 第1步：安装 Alembic

```bash
pip install alembic
```

添加到 `requirements.txt`：
```
alembic==1.13.1
```

### 第2步：初始化 Alembic

```bash
cd backend  # 进入项目后端目录
alembic init migrations
```

生成的目录结构：
```
backend/
├── alembic.ini           # Alembic 配置文件
└── migrations/
    ├── env.py           # 环境配置（需要修改）
    ├── script.py.mako   # 迁移脚本模板
    ├── README
    └── versions/        # 迁移脚本存放目录
```

### 第3步：配置 env.py

编辑 env.py，添加模型导入：

```python
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context
import os
import sys
from pathlib import Path

# ⭐ 添加项目根路径到 sys.path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# ⭐ 导入所有模型（确保 SQLModel 能识别）
from backend.db_models.chat_models import ChatSession, ChatMessage
from backend.db_models.setting_models import LLMSetting, DefaultSetting
# 添加其他模型...

# ⭐ 导入数据库引擎
from backend.core.database import engine
from sqlmodel import SQLModel

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ⭐ 设置 target_metadata
target_metadata = SQLModel.metadata

def run_migrations_offline() -> None:
    """离线模式：生成SQL脚本而不连接数据库"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """在线模式：连接数据库执行迁移"""
    # ⭐ 使用项目配置的 engine
    connectable = engine
    
    with connectable.connect() as connection:
        context.configure(
            connection=connection, 
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

### 第4步：配置 alembic.ini（可选）

如果使用独立配置文件，编辑 alembic.ini：

```ini
[alembic]
script_location = migrations
sqlalchemy.url = sqlite:///./data/app.db  # 数据库连接字符串

# 日志配置
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic
```

### 第5步：生成初始迁移

```bash
cd backend
alembic revision --autogenerate -m "initial_migration_create_tables"
```

### 第6步：执行初始迁移

```bash
alembic upgrade head
```

---

## 日常开发流程

### 标准工作流程

```
1. 修改模型 (db_models/*.py)
   ↓
2. 生成迁移脚本
   ↓
3. 审查迁移脚本
   ↓
4. 执行迁移
   ↓
5. 测试验证
   ↓
6. 提交代码
```

### 详细步骤

**1. 修改模型**

例如添加新字段：

```python
# backend/db_models/setting_models.py

class LLMSetting(SQLModel, table=True):
    __tablename__ = "llm_setting"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    provider: str = Field(index=True)
    model_name: str
    api_key: str
    
    # 新增字段
    timeout: int = Field(default=30, description="请求超时时间（秒）")
```

**2. 生成迁移**

```bash
cd backend
alembic revision --autogenerate -m "add_timeout_to_llm_setting"
```

**3. 审查生成的迁移文件**

打开 `migrations/versions/xxxxx_add_timeout_to_llm_setting.py`：

```python
def upgrade() -> None:
    # 确认生成的 SQL 是否正确
    op.add_column('llm_setting', sa.Column('timeout', sa.Integer(), nullable=False))

def downgrade() -> None:
    # 确认回滚逻辑是否正确
    op.drop_column('llm_setting', 'timeout')
```

**4. 执行迁移**

```bash
alembic upgrade head
```

**5. 验证**

```bash
# 查看当前版本
alembic current

# 查看历史
alembic history
```

---

## 常见场景操作

### 场景1：添加新表

**步骤：**

1. 创建新模型类
```python
# backend/db_models/new_model.py

class Task(SQLModel, table=True):
    __tablename__ = "task"
    
    id: Optional[int] = Field(default=None, primary_key=True)
    title: str
    status: str = Field(default="pending")
    created_at: datetime = Field(default_factory=datetime.now)
```

2. 在 env.py 中导入
```python
from backend.db_models.new_model import Task
```

3. 生成迁移
```bash
alembic revision --autogenerate -m "add_task_table"
```

4. 执行迁移
```bash
alembic upgrade head
```

### 场景2：重命名表

**方法A：修改模型并自动生成（推荐）**

```python
class LLMSetting(SQLModel, table=True):
    __tablename__ = "llm_setting"  # 指定新表名
    # ...
```

```bash
alembic revision --autogenerate -m "rename_llmconfig_to_llm_setting"
alembic upgrade head
```

**方法B：手动编写迁移**

```bash
alembic revision -m "rename_llmconfig_to_llm_setting"
```

编辑生成的文件：

```python
def upgrade() -> None:
    op.rename_table('llmconfig', 'llm_setting')

def downgrade() -> None:
    op.rename_table('llm_setting', 'llmconfig')
```

### 场景3：添加字段

**带默认值的字段（安全）：**

```python
class LLMSetting(SQLModel, table=True):
    # 新字段
    is_active: bool = Field(default=True)
```

```bash
alembic revision --autogenerate -m "add_is_active_to_llm_setting"
alembic upgrade head
```

**不带默认值的字段（需要数据迁移）：**

```python
# 方法1：添加时设为可选
new_field: Optional[str] = Field(default=None)

# 方法2：手动迁移时填充数据
```

手动迁移示例：

```python
def upgrade() -> None:
    # 1. 添加字段（允许空值）
    op.add_column('llm_setting', sa.Column('new_field', sa.String(), nullable=True))
    
    # 2. 填充默认数据
    op.execute("UPDATE llm_setting SET new_field = 'default_value'")
    
    # 3. 设置为非空
    op.alter_column('llm_setting', 'new_field', nullable=False)
```

### 场景4：删除字段

```python
# 在模型中删除字段
class LLMSetting(SQLModel, table=True):
    # old_field: str  # 注释或删除
    pass
```

```bash
alembic revision --autogenerate -m "remove_old_field_from_llm_setting"
alembic upgrade head
```

### 场景5：修改字段类型

**手动迁移（推荐）：**

```bash
alembic revision -m "change_api_key_to_text"
```

```python
def upgrade() -> None:
    # SQLite 不支持直接 ALTER COLUMN，需要重建表
    op.execute("""
        CREATE TABLE llm_setting_new (
            id INTEGER PRIMARY KEY,
            api_key TEXT NOT NULL,
            -- 其他字段...
        );
        
        INSERT INTO llm_setting_new SELECT * FROM llm_setting;
        DROP TABLE llm_setting;
        ALTER TABLE llm_setting_new RENAME TO llm_setting;
    """)

def downgrade() -> None:
    # 回滚逻辑
    pass
```

### 场景6：添加外键

```python
class ChatSession(SQLModel, table=True):
    # 添加外键关系
    config_id: int = Field(foreign_key="llm_setting.id")
```

```bash
alembic revision --autogenerate -m "add_foreign_key_to_chat_session"
alembic upgrade head
```

### 场景7：创建索引

**在模型中定义：**

```python
class LLMSetting(SQLModel, table=True):
    provider: str = Field(index=True)  # 自动创建索引
```

**手动迁移：**

```python
def upgrade() -> None:
    op.create_index('ix_llm_setting_provider', 'llm_setting', ['provider'])

def downgrade() -> None:
    op.drop_index('ix_llm_setting_provider', 'llm_setting')
```

---

## 迁移管理

### 查看状态

```bash
# 当前版本
alembic current

# 迁移历史
alembic history

# 详细历史（包含文件路径）
alembic history --verbose

# 查看特定范围
alembic history -r base:head
```

### 版本控制

```bash
# 升级到特定版本
alembic upgrade <revision_id>

# 升级到最新
alembic upgrade head

# 向前1步
alembic upgrade +1

# 向前N步
alembic upgrade +N

# 回滚到特定版本
alembic downgrade <revision_id>

# 回滚到初始状态
alembic downgrade base

# 回退1步
alembic downgrade -1
```

### 标记版本（不执行SQL）

当手动修改数据库或从其他源同步时：

```bash
# 标记当前数据库为特定版本
alembic stamp <revision_id>

# 标记为最新版本
alembic stamp head
```

### 生成SQL预览（不执行）

```bash
# 生成升级SQL
alembic upgrade head --sql > migration.sql

# 生成回滚SQL
alembic downgrade -1 --sql > rollback.sql
```

### 合并迁移（分支处理）

当多人开发产生分支时：

```bash
# 查看分支
alembic branches

# 合并两个分支
alembic merge <rev1> <rev2> -m "merge migrations"

# 执行合并后的迁移
alembic upgrade head
```

---

## 故障排查

### 常见错误及解决方案

**错误1：`Target database is not up to date`**

```bash
# 原因：数据库版本落后
# 解决：升级到最新
alembic upgrade head
```

**错误2：`Can't locate revision identified by 'xxxxx'`**

```bash
# 原因：迁移文件丢失或版本记录不一致
# 解决1：恢复丢失的迁移文件
# 解决2：重置版本标记
alembic stamp head
```

**错误3：`FAILED: Target database is not up to date`**

```bash
# 原因：数据库中有未应用的迁移
# 解决：
alembic current  # 查看当前版本
alembic history  # 查看历史
alembic upgrade head  # 升级
```

**错误4：`No module named 'backend'`**

```bash
# 原因：env.py 中路径配置错误
# 解决：在 env.py 中添加：
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
```

**错误5：`sqlalchemy.exc.NoReferencedTableError`**

```bash
# 原因：外键引用的表名不存在
# 解决：确保外键引用正确的表名
# 例如：foreign_key="llm_setting.id" 而不是 "llmconfig.id"
```

**错误6：`NameError: name 'sqlmodel' is not defined`**

```python
# 原因：迁移文件中使用了 sqlmodel 但未导入
# 解决：在迁移文件顶部添加
import sqlmodel
```

### 紧急回滚

如果迁移后出现问题：

```bash
# 方法1：回滚到上一个版本
alembic downgrade -1

# 方法2：回滚到特定版本
alembic current  # 查看当前版本
alembic downgrade <上一个正常的revision_id>

# 方法3：如果回滚失败，使用备份恢复数据库
cp backup/app.db data/app.db
alembic stamp <backup_version>
```

### 重置数据库（开发环境）

```bash
# 删除数据库
rm data/app.db

# 删除迁移历史
rm -rf migrations/versions/*

# 重新生成初始迁移
alembic revision --autogenerate -m "initial_migration"

# 执行迁移
alembic upgrade head
```

---

## 团队协作规范

### 迁移文件命名规范

```
<timestamp>_<简短描述>.py

✅ 好的命名：
- 20260204_add_user_table.py
- 20260204_rename_llmconfig_to_llm_setting.py
- 20260204_add_timeout_field.py

❌ 不好的命名：
- 123abc_migration.py
- new_changes.py
```

### Git 工作流

**1. 提交迁移文件**

```bash
git add migrations/versions/*.py
git commit -m "feat(db): add timeout field to llm_setting"
```

**2. 拉取代码后同步数据库**

```bash
git pull
cd backend
alembic upgrade head
```

**3. 解决迁移冲突**

当多人同时创建迁移时：

```bash
# 查看分支
alembic branches

# 方法1：合并迁移
alembic merge <rev1> <rev2> -m "merge migrations"

# 方法2：手动调整 down_revision
# 编辑迁移文件，修改 down_revision 指向正确的父版本
```

### 迁移审查清单

提交前检查：

- [ ] 迁移文件命名清晰
- [ ] `upgrade()` 和 `downgrade()` 都已实现
- [ ] 测试过升级和回滚
- [ ] 没有删除已发布的迁移文件
- [ ] 数据迁移逻辑正确（如有）
- [ ] 外键关系正确
- [ ] 索引已创建（如需要）

### 版本发布流程

```bash
# 1. 开发环境测试
alembic upgrade head
# 运行测试...

# 2. 生成SQL预览（用于生产环境审查）
alembic upgrade head --sql > deploy/migration_v1.2.0.sql

# 3. 在预发布环境测试
# 备份数据库
cp production.db production.db.backup
# 执行迁移
alembic upgrade head

# 4. 生产环境部署
# 备份 + 迁移
# 验证
```

---

## 最佳实践

### ✅ 推荐做法

1. **总是使用 `--autogenerate`**（然后审查）
2. **迁移前备份数据库**
3. **测试回滚脚本**
4. **小步迭代**（一个迁移做一件事）
5. **添加注释**说明复杂迁移逻辑
6. **不删除已发布的迁移文件**
7. **使用描述性的消息**

### ❌ 避免做法

1. **不要手动修改数据库后忘记同步迁移**
2. **不要在生产环境直接修改迁移文件**
3. **不要跳过版本执行**
4. **不要在迁移中使用绝对导入**
5. **不要在 `upgrade()` 中使用 ORM 操作**（使用原生SQL）

---

## 附录：常用操作示例

### 数据迁移示例

```python
def upgrade() -> None:
    # 添加字段
    op.add_column('llm_setting', sa.Column('is_active', sa.Boolean(), nullable=True))
    
    # 填充默认值
    op.execute("UPDATE llm_setting SET is_active = 1")
    
    # 设置为非空
    op.alter_column('llm_setting', 'is_active', nullable=False)

def downgrade() -> None:
    op.drop_column('llm_setting', 'is_active')
```

### 批量操作示例

```python
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # 批量修改
    connection = op.get_bind()
    connection.execute(
        sa.text("UPDATE llm_setting SET provider = 'openai' WHERE provider = 'old_name'")
    )
```

### 条件迁移示例

```python
def upgrade() -> None:
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # 检查表是否存在
    if 'old_table' in inspector.get_table_names():
        op.rename_table('old_table', 'new_table')
```

---

**📌 快速开始清单**

```bash
# 1. 安装
pip install alembic

# 2. 初始化
cd backend
alembic init migrations

# 3. 配置 env.py（导入模型）

# 4. 生成初始迁移
alembic revision --autogenerate -m "initial_migration"

# 5. 执行迁移
alembic upgrade head

# 日常使用：
# - 修改模型后：alembic revision --autogenerate -m "描述"
# - 应用迁移：alembic upgrade head
# - 回滚：alembic downgrade -1
```