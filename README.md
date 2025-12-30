

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

### v0.2.1 
 - feat:      启动项与热重载  
 - fix:       chatbox 历史聊天记录不显示

### v0.2.0
 - build:     前后端分离

---

## 三、项目结构

```
myPCAgent/
│
├── .gitignore
├── README.md
├── start.bat
├── clear_cache.py
├── tree.txt
│
├── backend/                     # FastAPI 后端服务
│   ├── __init__.py
│   ├── main.py                  # 应用入口
│   │
│   ├── api/
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── router.py        # API 路由聚合
│   │       └── endpoints/
│   │           ├── __init__.py
│   │           └── greeting.py  # 具体接口实现
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── back_config.py       # 配置加载逻辑
│   │   └── back_config.yaml     # 后端配置文件
│   │
│   ├── core/                    # 核心业务逻辑
│   │   ├── __init__.py
│   │   ├── bootstrap.py         # 应用初始化
│   │   ├── database.py          # 数据库连接
│   │   │
│   │   ├── services/            # 业务服务层
│   │   │   ├── __init__.py
│   │   │   └── greeting_service.py
│   │   │
│   │   └── tools/               # 工具函数（可后续扩展）
│   │       └── __init__.py
│   │
│   ├── db_models/               # 数据库模型（SQLAlchemy / Pydantic）
│   │   └── __init__.py
│   │
│   ├── data/                    # 静态数据或种子数据（可选）
│   ├── logs/                    # 日志输出目录（运行时生成）
│   └── migrations/              # 数据库迁移脚本（如 Alembic）
│       └── __init__.py
│
├── config/                      # 全局共享配置
│   ├── __init__.py
│   ├── env_config.py            # 环境配置加载
│   └── env_config.yaml          # 全局环境变量定义
│
├── frontend/                    # Gradio 前端应用
│   ├── __init__.py
│   ├── app.py                   # 前端主入口
│   │  
│   ├── handlers/   
│   │   └── dashboard.py         # 前端事件处理逻辑
│   │
│   └── ui/                      # UI 组件定义
│       └── dashboard.py         # Gradio 界面布局
│
└── shared/                      # 前后端共享代码（纯 Python，无框架依赖）
    └── v1/
        ├── __init__.py
        └── schemas.py           # Pydantic 模型（如请求/响应结构）
  
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

## 五、程序启动

以下是 **Your Agent Project v0.2.0 的完整程序启动流程说明**，包含文字描述与流程图（以 ASCII 形式呈现），清晰展示从用户执行命令到前后端就绪的全过程。


### 1. 用户触发总启动器
```bash
python main.py
```

### 2. 总启动程序（`main.py`）
- 位于项目根目录；  
- 负责 **并行启动后端（FastAPI）和前端（Gradio）**；  
- 使用 `subprocess` 创建两个独立子进程；  
- 监听 `Ctrl+C` 信号，实现优雅关闭。  
  
### 3. 衍生出后端启动程序（`backend/main.py`）  
 - 启动 backend/main.py  
 - 立即调用 bootstrap.py 执行启动引导  
 - 引导完成后，启动 FastAPI 应用，并监听默认地址 127.0.0.1:8000 上的 HTTP 请求  

### 4. 启动引导程序（`backend/core/bootstrap.py`）  
这是后端初始化的核心，按顺序执行：  
1. **加载配置**：通过 `ConfigLoader` 读取 `config/env_config.yaml`；  
2. **设置日志系统**：初始化 `runtime.log` 和（可选）`debug.log`；  
3. **检查数据库**：  
   - 若 `data/agent.db` 不存在 → 执行初始迁移（`migrations/v1_initial.py`）；  
   - 若存在但 Schema 版本低于期望值 → 自动升级（如运行 `v2_add_capability_type.py`）；  
4. **验证关键路径**：确保 `logs/`、`data/` 目录存在；  
5. **完成引导**，FastAPI 正式就绪。  

> ✅ **注意**：`bootstrap.py` 是 **同步阻塞执行** 的，确保服务在完全初始化后才接受请求。

### 5. 衍生出前端启动程序（`frontend/app.py`）  
- 启动 Gradio 应用；  
- 默认监听 `127.0.0.1:7860`。

---

### 📊 启动流程图（ASCII）

```text
+---------------------+
|   User runs:        |
|   python main.py    |
+----------+----------+
           |
           v
+----------+----------+
|   main.py (Root)    |
|  ┌───────────────┐  |
|  │ Start Backend │──┼───▶ backend/main.py
|  └───────────────┘  |
|  ┌───────────────┐  |
|  │ Start Frontend│──┼───▶ frontend/app.py
|  └───────────────┘  |
+----------+----------+
           |
           | (Graceful shutdown on Ctrl+C)
           ▼
     [Both processes terminate]
```

### 后端内部引导流程（`backend/main.py` → `bootstrap.py`）

```text
backend/app.py
       │
       ▼
Load ConfigLoader from settings.py
       │
       ▼
Call bootstrap.initialize()
       │
       ├──▶ Load env_config.yaml
       │
       ├──▶ Setup logging:
       │      ├── runtime.log (INFO+)
       │      └── debug.log (DEBUG+, if enabled)
       │
       ├──▶ Ensure data/ and logs/ exist
       │
       └──▶ Database bootstrap:
              ├── Check agent.db exists?
              │     ├── No → Run v1_initial migration
              │     └── Yes → Check schema version
              │            ├── Match → OK
              │            └── Lower → Run pending migrations
              │
              ▼
       FastAPI server starts on http://127.0.0.1:8000
```

### 前端启动流程（`frontend/app.py`）

```text
frontend/app.py
       │
       ▼
Initialize Gradio Blocks with Tabs:
       ├── 💬 Chat       → calls /api/v1/chat
       ├── 🧠 Capabilities → calls /api/v1/capabilities
       ├── 🛠️ Tools      → calls /api/v1/tools
       └── 📜 Logs       → calls /api/v1/logs
       │
       ▼
Launch Gradio on http://127.0.0.1:7860
       │
       ▼
Open browser (or print URL)
```

---

### 🔁 进程关系总结

| 进程 | 启动方式 | 依赖 | 通信方式 |
|------|--------|------|--------|
| **`main.py`** | 用户直接运行 | 无 | 父进程，管理子进程生命周期 |
| **`backend/main.py`** | `main.py` 通过 `subprocess` 启动 | `env_config.yaml` | 提供 HTTP API（`/api/v1/...`） |
| **`frontend/app.py`** | `main.py` 通过 `subprocess` 启动 | 后端 API 可用性 | 通过 HTTP 调用后端接口 |

## 六、启动方式 

> 双击运行 `start.bat`，或者在命令行/PowerShell 中执行 `.\start.bat`  



