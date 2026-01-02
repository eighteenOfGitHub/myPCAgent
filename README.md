

# Your Agent Project — 技术文档（v0.2.x）

---

## 一、项目介绍

**Your Agent Project** 是一个面向个人 PC 的本地 AI Agent 框架，旨在提供：

- **能力路由**：统一管理本地/远程的 LLM、Embedding、工具等 **系统能力**，支持优先级调度与能力匹配；
- **工具集成**：通过 MCP（Model Calling Protocol）标准接入外部工具（如搜索、代码执行、语音）；
- **对话管理**：记录会话上下文，支持多轮交互与工具调用链；
- **配置持久化**：所有 **系统能力的元数据**（如模型名称、端点、状态等）存储于本地 SQLite 数据库；
- **可观测性**：系统运行日志以 **结构化文本文件形式备份**，便于调试与审计；
- **Web 管理界面**：基于 **Gradio** 提供交互式前端，支持能力配置管理、日志查看、实时聊天。

---

## 二、版本新增

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

## 三、项目结构

```
myPCAgent/
├── .gitignore
├── clear_cache.py
├── README.md
├── start.bat                 # 项目总启动脚本 (Windows)
├── tree.txt
│
├── backend/                  # 后端服务 (FastAPI)
│   ├── main.py               # 后端主入口：初始化 DB、配置、路由，启动 FastAPI
│   ├── __init__.py
│   │
│   ├── api/
│   │   ├── router.py         # API 路由聚合器
│   │   └── endpoints/        # API 端点定义
│   │       ├── chat.py
│   │       ├── greeting.py
│   │       ├── health.py
│   │       ├── llm_setting.py
│   │       └── user_preference.py
│   │
│   ├── core/                 # 核心模块
│   │   ├── database.py       # 数据库初始化
│   │   ├── logger.py         # 日志系统配置
│   │   └── config/
│   │       ├── back_config.py    # 后端配置加载器
│   │       └── back_config.yaml  # 后端配置文件
│   │
│   ├── data/
│   │   └── pcagent.db        # SQLite 数据库文件 (存储能力/用户配置元数据)
│   │
│   ├── db_models/            # SQLModel 数据模型
│   │   ├── chat_models.py
│   │   └── user_config.py
│   │
│   ├── logs/
│   │   └── app.log           # 应用运行日志
│   │
│   ├── middleware/
│   │   └── logging_middleware.py # 请求日志中间件
│   │
│   └── services/             # 业务逻辑服务层
│       ├── chat_service.py
│       ├── greeting_service.py
│       ├── llm_setting_service.py
│       └── user_preference_service.py
│
├── config/                   # 全局共享配置
│   ├── env_config.py
│   └── env_config.yaml
│
├── docs/                     # 项目文档
│   └── ...
│
├── frontend/                 # 前端应用 (Gradio)
│   ├── app.py                # 前端主入口：构建 UI 并启动 Gradio
│   ├── __init__.py
│   │
│   ├── handlers/             # 前端事件处理器
│   │   ├── chat_handler.py
│   │   ├── dashboard.py
│   │   └── llm_models_setting.py
│   │
│   ├── ui/
│   │   └── main_layout.py    # 主界面布局
│   │
│   └── pages/                # 各功能页面组件
│       ├── agent.py
│       ├── chat.py
│       ├── dashboard.py
│       ├── general_setting.py
│       ├── llm_models_setting.py
│       └── settings.py
│
└── shared/                   # 前后端共享代码
    ├── schemas.py            # Pydantic/SQLModel 模型 (用于 API Schema)
    └── __init__.py
  
```

## 四、技术选型与配置管理  

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

## 五、程序启动

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

你可以将以上内容直接复制到你的 `README.md` 文件中，替换原有的第三和第五部分。这能更准确地反映你当前项目的实际情况。

## 六、相关命令



> **运行**		双击运行 `start.bat`，或者在命令行/PowerShell 中执行 `.\start.bat`  
>
> **清理缓存**	`python clear_cache.py`
>
> **生成结构树**    `tree /F > tree.txt  `



