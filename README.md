# Your Agent Project — 技术文档（v0.2.x）

---

## 🧭 一、项目介绍

**Your Agent Project** 是一个面向个人 PC 的本地 AI Agent 框架，旨在提供：

- **能力路由**：统一管理本地/远程的 LLM、Embedding、工具等 **系统能力**，支持优先级调度与能力匹配；
- **工具集成**：通过 MCP（Model Calling Protocol）标准接入外部工具（如搜索、代码执行、语音）；
- **对话管理**：记录会话上下文，支持多轮交互与工具调用链；
- **配置持久化**：所有 **系统能力的元数据**（如模型名称、端点、状态等）存储于本地 SQLite 数据库；
- **可观测性**：系统运行日志以 **结构化文本文件形式备份**，便于调试与审计；
- **Web 管理界面**：基于 **Gradio** 提供交互式前端，支持能力配置管理、日志查看、实时聊天。

---

## 🧩 二、版本新增

### v0.2.12 chatbot功能实现

 - feat：`DefaultSettingService`、`LLMSettingService` 添加缓存机制，减少数据库访问频率，提高性能；同时给chat_service暴露接口，为以便后chat_service调用
 - feat（未实现）：在 `LLMSettingService` 中新增 `get_active()` 方法，用于获取当前激活的 LLM 配置


### v0.2.11 前端不同页面间状态共享

 - factor：llm_setting的数据初始化从llm_setting_ui迁移到main_layout_ui中，避免多次请求后端接口
 - feat: llm_setting_ui返回状态引用，供主布局监听，实现不同页面间状态共享
 - feat: chat_ui实现default_llm_config_id状态更新

### v0.2.10 default_setting相关

 - factor：重命名 preference_setting 为 default_setting


### v0.2.9 数据库版本管理

 - feat: 集成 Alembic 实现数据库版本管理与迁移
 - docs: 编写 Alembic 使用手册，指导开发者如何创建/应用迁移脚本

### v0.2.8 preference_setting_ui相关

 - feat: 下拉框默认模型添加（default model）用于显示区别
 - feat：重新设置默认模型后自动刷新下拉框
 - feat：preference_setting_ui界面美化（按钮同行，提示语自动消失）
 - feat：LLM模型删除功能（带下拉框选择与确认按钮）
 - factor：preference_setting_ui中default_llm部分迁移到llm_setting_ui中，使用gr.state管理数据，减少数据重复获取，提高前端性能

### v0.2.7
- feat：设置页面加载时数据自动加载
- fix: api_key传输前加密功能缺失，已补齐
- factor：代码文件名加上功能后缀（例如：ui/user.py -> ui/user_ui.py）
- factor：统一后端路由获取路径（来源env_config），并将要求写入前端ai开发规范中

### v0.2.6
- feat：默认下拉框内容功能获取实现
- feat：下拉框刷新实现
- feat：加载下拉框默认
- feat：保存默认设置

### v0.2.5
- feat: 前端提交 LLM 配置前使用 Fernet 对 api_key 加密（shared/crypto）
- feat: 后端 LLMSettingService 解密后调用，数据库存密文
- chore: EnvConfig 缺失 FERNET_KEY 时自动生成并写回 env_config.yaml，确保前后端同钥
- docs: 补充 EnvConfig 与监控/运维说明

### v0.2.4
- refactor: shared中schemas的响应体模型按照api/endpoint拆分到shared下的不同文件，按照对应endpoint命名
- refactor: 移除热重载功能，简化启动流程

### v0.2.3
- feat: 设置页面显示已保存模型

### v0.2.2
- bulid: 日志系统
- faet: 前端分页
- feat: 添加大模型配置

### v0.2.1 
 - feat: 启动项与热重载  
 - fix: chatbox 历史聊天记录不显示

### v0.2.0
 - build: 前后端分离

---

## 🗂️ 三、项目结构

```
.
|   .gitignore
|   clear_cache.py
|   generate_tree.bat
|   README.md
|   start.bat
|   start_debug.bat
|   tree.txt
|   
+---backend
|   |   alembic.ini
|   |   main.py
|   |   __init__.py
|   |   
|   +---api
|   |   |   router.py
|   |   |   __init__.py
|   |   |   
|   |   \---endpoints
|   |           chat_api.py
|   |           default_setting_api.py
|   |           greeting_api.py
|   |           health_api.py
|   |           llm_setting_api.py
|   |           __init__.py
|   |           
|   +---core
|   |   |   database.py
|   |   |   logger.py
|   |   |   __init__.py
|   |   |   
|   |   +---config
|   |   |       back_config.py
|   |   |       back_config.yaml
|   |   |       log_config.yaml
|   |   |       __init__.py
|   |   |       
|   |   \---utils
|   +---data
|   |       pcagent.db
|   |       
|   +---db_models
|   |       chat_models.py
|   |       setting_models.py
|   |       __init__.py
|   |       
|   +---logs
|   |       app.log
|   |       
|   +---middleware
|   |       logging_middleware.py
|   |       
|   +---migrations
|   |   |   env.py
|   |   |   README
|   |   |   script.py.mako
|   |   |   
|   |   \---versions
|   |           2c572c105ed4_rename_all_tables_to_snake_case.py
|   |           8f2b36a21551_initial_migration_create_tables.py
|   |           
|   \---services
|           chat_service.py
|           default_setting_service.py
|           greeting_service.py
|           llm_setting_service.py
|           __init__.py
|           
+---config
|       env_config.py
|       env_config.yaml
|       __init__.py
|       
+---docs
|   +---development
|   |   +---services
|   |   \---sys
|   |           AI编程规范.md
|   |           Alembic 数据库版本管理手册.md
|   |           前端服务（gradio）开发规范与流程速查手册.md
|   |           后端服务开发规范与流程速查手册.md
|   |           日志系统开发规范文档.md
|   |           
|   +---notes
|   |   |   ideas.md
|   |   |   
|   |   +---notes_from_error
|   |   |       database_note.md
|   |   |       logging_note.md
|   |   |       project_note.md
|   |   |       python_note.md
|   |   |       
|   |   \---systematic_note
|   |           github代码管理与协作开发规范.md
|   |           
|   +---plans
|   |       26_2_1_chat.md
|   |       
|   \---references
|       \---chatbot
|           |   info.md
|           |   modelscope_gradio.py
|           |   
|           \---md_images
|                   chatbot_ui_index.png
|                   chatbot_ui_qa.png
|                   
+---frontend
|   |   app.py
|   |   __init__.py
|   |   
|   +---handlers
|   |       chat_handler.py
|   |       dashboard_handler.py
|   |       default_setting_handler.py
|   |       llm_setting_handler.py
|   |       
|   \---ui
|       |   main_layout_ui.py
|       |   
|       \---pages
|               agent_ui.py
|               chat_ui.py
|               dashboard_ui.py
|               default_setting_ui.py
|               llm_setting_ui.py
|               settings_ui.py
|               __init__.py
|               
\---shared
        chat_schemas.py
        crypto.py
        default_setting_schemas.py
        general_schemas.py
        greeting_schemas.py
        llm_setting_schemas.py
        __init__.py
        
```

## 🧪 四、技术选型与配置管理  

| 类别 | 技术/库 | 版本/说明 | 选型理由 |
|------|--------|----------|--------|
| **核心语言** | Python | ≥ 3.10 | 生态丰富，AI 工具链成熟，开发效率高 |
| **后端框架** | FastAPI | 最新稳定版 | ✅ 高性能（Starlette + Pydantic）<br>✅ 自动生成 OpenAPI 文档<br>✅ 异步原生支持（适合 LLM 流式调用）<br>✅ 与 SQLModel 深度集成 |
| **前端框架** | Gradio | ≥ 4.0 | ✅ 原生 `gr.ChatInterface` 支持流式聊天<br>✅ `gr.Dataframe` 提供强大表格交互（能力/工具管理）<br>✅ 快速构建 AI 交互界面<br>✅ 可独立部署，通过 HTTP 调用后端 API |
| **数据库** | SQLite | 内置于 Python | ✅ 零配置、单文件、ACID<br>✅ 完美适配本地单机场景<br>✅ 仅存储 **能力/工具元数据**（非日志、非模型）<br>❌ 不适用于高并发或多用户（但本项目无需） |
| **ORM / 数据模型** | SQLModel | 最新稳定版 | ✅ **核心选择**：<br> - 统一 Pydantic + SQLAlchemy<br> - `SQLModel` 类 = 数据库表 = API Schema<br> - 自动序列化/反序列化，消除游标管理<br> - FastAPI 官方推荐<br>✅ 所有表结构定义于 `backend/core/db_models/` |
| **日志系统** | Python `logging` + `RotatingFileHandler` | 标准库 | ✅ **仅使用文件备份**，不存数据库<br>✅ 分离 `runtime.log`（INFO+）与 `debug.log`（DEBUG+）<br>✅ 支持日志轮转（防磁盘爆满）<br>✅ 格式可配置，兼容 `grep`/`tail` 等工具 |
| **配置管理** | PyYAML + 自定义 `ConfigLoader` | `pyyaml>=6.0` | ✅ 配置集中于 `config/env_config.yaml`<br>✅ 动态加载 `system.version`、路径、日志级别等<br>✅ 避免硬编码，支持环境差异化部署 |
| **API 规范** | RESTful + JSON | — | ✅ `/api/v1/...` 路径清晰<br>✅ 请求/响应体由 SQLModel 自动生成 Pydantic 模型<br>✅ 兼容未来扩展（v2, v3...） |
| **共享类型** | `shared/v1/schemas.py` | 由 SQLModel 导出 | ✅ 前后端共用同一套数据结构定义<br>✅ 避免类型不一致导致的 bug |
| **版本控制** | 语义化版本（SemVer） | `vx.x.x` | ✅ `VERSION` 文件 + `env_config.yaml` 声明版本<br>✅ 数据库 Schema 版本独立管理（用于迁移） |
| **代码风格** | Black + isort | — | ✅ 自动格式化，保证代码一致性（建议加入 CI） |
| **可选：打包/分发** | PyInstaller / Docker | — | ✅ 未来可打包为单文件 EXE 或容器镜像 |

---

### EnvConfig
- 文件：`config/env_config.py` / `config/env_config.yaml`。
- 作用：集中管理前后端共享参数（如主机端口、API 基础地址、CORS 源）。
- 安全：包含 `FERNET_KEY`（对称密钥），用于前后端加解密；缺失时自动生成并写回 YAML，需确保前后端读取同一份密钥。（建议重新生成）

---

## 🚀 五、程序启动

Your Agent Project 的启动流程涉及**后端 (FastAPI)** 和**前端 (Gradio)** 两个独立但协同的服务。推荐通过根目录下的 `start.bat` 脚本一键启动。

#### 1. 总启动器 (`start.bat`)
这是用户交互的唯一入口。
- **作用**：并行启动后端和前端服务。
- **执行方式**：
  - **Windows**: 双击 `start.bat` 或在 PowerShell/CMD 中运行 `.\start.bat`。

#### 2. 后端启动流程 (`backend/main.py`)
当 `start.bat` 触发后端启动时，会执行以下步骤：
1.  **初始化日志系统**：根据 `core/config/log_config.yaml` 配置日志格式与输出。
2.  **初始化数据库**：调用 `core/database.py` 连接 `data/pcagent.db`，并确保表结构存在。
3.  **创建 FastAPI 应用**：
    - 注册 CORS 中间件，允许前端 (`frontend/`) 跨域访问。
    - 注册自定义 `LoggingMiddleware` 以记录请求。
    - 挂载 API 路由 (`/api`)，路由定义位于 `api/endpoints/`。
4.  **启动服务器**：使用 Uvicorn 在 `127.0.0.1:8000` (或配置文件指定端口) 上启动 HTTP 服务。

> ✅ **关键点**：后端是一个标准的 RESTful API 服务器，为前端提供所有数据和业务逻辑接口。

#### 3. 前端启动流程 (`frontend/app.py`)
当 `start.bat` 触发前端启动时，会执行以下步骤：
1.  **构建 Gradio 应用**：
    - 使用 `ui/main_layout.py` 和 `pages/` 下的组件构建完整的 Web UI。
    - UI 包含多个标签页：聊天 (`chat`)、仪表盘 (`dashboard`)、LLM 模型设置 (`llm_models_setting`) 等。
2.  **连接后端**：前端 UI 组件通过 HTTP 请求（如 `fetch`）调用后端 `http://127.0.0.1:8000/api/...` 的 API。
3.  **启动服务器**：Gradio 在 `127.0.0.1:7860` (默认端口) 上启动一个 Web 服务器，并自动在浏览器中打开应用。

> ✅ **关键点**：前端是一个独立的 Web 应用，它不处理核心业务，只负责展示和用户交互，所有状态都通过 API 与后端同步。

#### 📊 启动流程图（ASCII）
```
+---------------------+
| User runs:          |
| .\start.bat         |
+----------+----------+
           |
           v
+----------+----------+
| start.bat (Root)    |
|                     |
| ┌───────────────┐   |
| │ Start Backend │───┼───▶ python backend/main.py
| └───────────────┘   |      (Serves on http://127.0.0.1:8000)
|                     |
| ┌───────────────┐   |
| │ Start Frontend│───┼───▶ python frontend/app.py
| └───────────────┘   |      (Serves on http://127.0.0.1:7860)
|                     |
+---------------------+
           |
           | (Graceful shutdown on Ctrl+C)
           ▼
    [Both processes terminate]
```

#### 🔁 进程关系总结
| 进程              | 启动方式         | 依赖               | 通信方式                   |
| ----------------- | ---------------- | ------------------ | -------------------------- |
| `start.bat`       | 用户直接运行     | 无                 | 父进程，管理子进程生命周期 |
| `backend/main.py` | `start.bat` 启动 | `config/`, `data/` | 提供 HTTP API (`/api/...`) |
| `frontend/app.py` | `start.bat` 启动 | 后端 API 可用性    | 通过 HTTP 调用后端接口     |

---

## 🧰 六、相关命令

| 命令 | 说明 |
|------|------|
| `.\start.bat` | 启动后端 (FastAPI @ 8000) 和前端 (Gradio @ 7860) |
| `python backend/main.py` | 单独启动后端服务 |
| `python frontend/app.py` | 单独启动前端服务 |
| `python clear_cache.py` | 清理 Python 缓存文件 (`__pycache__`, `.pyc` 等) |
| `.\generate_tree.bat` | 生成项目结构树并保存到 `tree.txt` |

> **快速启动**：双击 `start.bat` 或在命令行执行 `.\start.bat`  
> **清理缓存**：`python clear_cache.py`  
> **生成结构树**：`.\generate_tree.bat`

## 🛡️ 六、监控与运维
- 数据库查看：推荐使用 **DBeaver**（跨平台，支持 SQLite/MySQL/PostgreSQL 等），可直观浏览表结构与数据。
- 日志查看（app.log）：可用命令行实时查看（Linux/Mac：`tail -f backend/logs/app.log`，Windows PowerShell：`Get-Content backend/logs/app.log -Wait`），或使用日志查看工具（如 lnav/BareTail/IDE 内置 Log Viewer）
-