
# 🌲Your PC Agent

一个面向个人使用的本地智能 PC 自动化代理，基于 LLM 实现任务理解与执行，支持多模型调度、上下文感知和持久化记录。

目前正在尝试构建属于自己的PC Agent，“哐哧哐哧”构建中  
I'm currently building my own PC Agent with clangling and clanking  

---

## ✨ 核心功能（v0.1.0）

- **双模 LLM 支持**：可同时接入在线模型（如 qwen-plus）和本地模型（如 Ollama 的 qwen2.5:7b）
- **智能路由**：根据任务类型（通用 / 编码 / 工具调用）自动选择最优模型
- **会话上下文管理**：自动注入 Session ID，支持跨请求上下文追踪
- **持久化存储**：使用线程安全的 SQLite 记录对话日志与元数据

## ▶️ 快速开始

### 1. 克隆项目
```bash
git clone https://github.com/eighteenOfGitHub/myPCAgent.git
cd PCAgent
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置模型与行为
#### 最简 `llm_config.yaml` 示例：
```yaml
# config/llm_config.yaml
# 千问系列模型：https://help.aliyun.com/zh/model-studio/models
# 查看LiteLLM支持的提供商和模型：https://docs.litellm.ai/docs/providers

llm_pool:
  - name: "gpt-oss:120b-cloud-by-ollama"
    model: "ollama/gpt-oss:120b-cloud"
    type: "online"
    tags: ["general", "chat"]
    enabled: true
    api_base: "http://localhost:11434"
    api_key_env: null
    priority: 10
	
	...

  # - name: "gpt-4o-mini-route"         # (str) 在配置和日志中引用此模型的唯一标识
  #   model: "gpt-4o-mini"              # (str) 传递给 litellm 的实际模型名称
  #   type: "online"                    # (str) 模型部署类型，可选项: "local"(本地), "online"(远程API)
  #   tags: ["route"]                   # (List[str]) 标签，常见可选项: "general"(通用), "chat"(聊天), "coding"(代码),  "reasoning"(推理),
                                                                      #"route"(路由), "tts"(文本转语音), "asr"(自动语音识别)
  #   enabled: true                     # (bool) 启用状态，设为 true 表示此模型可用
  #   api_base: null                    # (Optional[str]) API 基础地址，null 表示使用 litellm 预设的默认地址
  #   api_key_env: "OPENAI_API_KEY"     # (str) API 密钥环境变量名，从该变量读取密钥
  #   priority: 15                      # (int) 调用优先级，数值越小优先级越高 (15 表示相对较低)

routing:
  default_mode: "online" # 可以是 online 或 local
  selection_strategy: "priority" # 当前仅支持 priority
  retry_on_failure: true
  max_total_attempts: 3 # 包括 litellm 内部重试

# --- 更新 defaults.mapping 以包含新的任务类型 ---
defaults:
  mapping:
    general:
      online: "qwen-plus-online"
      local: "qwen3:8b-local"
    # ...
```

> 💡 请确保设置环境变量（如 `DASHSCOPE_API_KEY`）或本地模型已运行（如 `ollama serve`）。

### 4. 启动服务
```bash
python -m pcagent.main
```
访问：
- Web UI：http://localhost:8000/

## 🛠️ 项目结构亮点

- **模块化设计**：`agents/`、`core/`、`services/` 分层清晰
- **配置驱动**：Pydantic 模型校验，避免无效配置
- **安全数据库**：`DatabaseManager` 封装连接池与事务
- **可扩展路由**：`LLMAgentRouter` 支持策略插拔
- ...

## 📅 下一步计划（v0.2.0+）

- 支持自定义工具函数（如文件操作、系统命令）
- 实现对话窗口与历史聊天记录
- 实现可插拔MCP服务
- 完善可视化界面

## 📜 License

MIT © eighteen
