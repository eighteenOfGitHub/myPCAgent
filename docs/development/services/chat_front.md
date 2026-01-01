
## 🧭 第一阶段：前端需求分析（已完成 ✅）

### ✅ 1. 项目目标
构建一个 **桌面级多页面 Gradio 应用**，作为 FastAPI 后端的配套前端，支持：
- 多功能页面切换（Chat / Agent / Settings / Dashboard）
- 与后端 API 深度集成（会话管理、流式聊天、配置读写）
- 良好的用户体验（响应式布局、状态保持、错误处理）

---

### ✅ 2. 功能模块划分

| 页面 | 核心功能 | 依赖后端 API |
|------|--------|-------------|
| **🏠 Dashboard** | 系统概览、快捷入口、运行状态 | `/health`, `/stats`（可选） |
| **💬 Chat** | 会话管理 + 流式对话 | `/chat/sessions`, `/chat/stream`, `/chat/turn` |
| **🤖 Agent** | 智能体创建/编辑/调试（未来） | （预留） |
| **⚙️ Settings** | LLM 配置管理、API Key 设置 | `/llm/configs`, `/env`（可选） |

> 🔜 当前重点：**先完成 Chat 页面**，其他页面做占位。

---

### ✅ 3. 技术选型
- **框架**：Gradio `Blocks`（非 `Interface`，因需复杂布局）
- **路由方案**：`gr.Tabs`（模拟多页面）
- **状态管理**：`gr.State()`（页面内）+ 全局 State（谨慎使用）
- **通信方式**：`requests` 调用 FastAPI（JSON/SSE）
- **流式支持**：`.queue()` + generator handler

---

### ✅ 4. 非功能需求
- **可拓展性**：新增页面 ≤ 3 步
- **可维护性**：UI 与逻辑分离（handler 模式）
- **健壮性**：网络错误提示、加载状态
- **开发体验**：热重载、dev/prod 配置分离

---

## 🚀 第二阶段：实现流程（分步推进）

我们将按以下 **5 个步骤** 逐步实现：

---

### 🔹 步骤 1：重构项目结构（目录标准化）

```bash
frontend/
├── app.py                     # 启动入口（不变）
├── ui/
│   ├── main_layout.py         # 👈 新增：Tabs 主布局
│   └── pages/
│       ├── __init__.py
│       ├── dashboard.py       # 主页（简单占位）
│       ├── chat.py            # 👈 重点实现
│       ├── agent.py           # 占位
│       └── settings.py        # 占位
└── handlers/
    ├── __init__.py
    ├── base_handler.py        # 封装 requests + 错误处理
    └── chat_handler.py        # 👈 重点实现
```

> ✅ 执行：创建上述文件（内容先为空或简单占位）

---

### 🔹 步骤 2：实现主布局（`main_layout.py`）

目标：搭建 Tabs 框架，各页面仅显示标题。

```python
# frontend/ui/main_layout.py
import gradio as gr
from frontend.ui.pages import dashboard, chat, agent, settings

def create_gradio_interface():
    with gr.Blocks(title="PC Agent", theme=gr.themes.Soft()) as demo:
        with gr.Tabs():
            with gr.Tab("🏠 Dashboard"):
                dashboard.render()
            with gr.Tab("💬 Chat"):
                chat.render()
            with gr.Tab("🤖 Agent"):
                agent.render()
            with gr.Tab("⚙️ Settings"):
                settings.render()
    return demo
```

每个页面 `render()` 函数示例（`dashboard.py`）：
```python
def render():
    gr.Markdown("# 🏠 Dashboard\n欢迎使用 PC Agent！")
```

> ✅ 验证：启动后能看到 4 个 Tab，点击可切换。

---

### 🔹 步骤 3：实现 Chat 页面 UI（`chat.py`）

目标：完成左侧会话面板 + 右侧聊天窗口布局。

```python
# frontend/ui/pages/chat.py
def render():
    with gr.Row():
        # 左侧：会话控制
        with gr.Column(scale=1, min_width=180):
            gr.Markdown("### 💬 会话")
            session_dropdown = gr.Dropdown(label="历史会话", choices=[], interactive=True)
            new_session_btn = gr.Button("🆕 新建会话", variant="primary")
            delete_session_btn = gr.Button("🗑️ 删除会话", variant="stop")
            
            gr.Markdown("### ⚙️ 模型")
            model_info = gr.Textbox(label="当前模型", interactive=False)

        # 右侧：聊天区
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(height=500, label="对话")
            msg_input = gr.Textbox(label="消息", placeholder="输入后按回车...", lines=1)
            send_btn = gr.Button("发送消息", variant="primary")

    # 返回控件引用（用于事件绑定）
    return {
        "session_dropdown": session_dropdown,
        "new_session_btn": new_session_btn,
        "delete_session_btn": delete_session_btn,
        "chatbot": chatbot,
        "msg_input": msg_input,
        "send_btn": send_btn,
        "model_info": model_info,
    }
```

> ✅ 此时 UI 完整，但无交互。

---

### 🔹 步骤 4：实现 Chat 业务逻辑（`chat_handler.py`）

目标：对接你的 FastAPI，实现：
- 加载会话列表
- 新建会话
- 流式发送消息

#### 关键函数设计：

```python
# frontend/handlers/chat_handler.py

def load_session_list():
    """获取所有会话 -> 用于 Dropdown"""
    ...

def create_new_session():
    """POST /api/chat/sessions -> 返回新 session_id"""
    ...

def load_messages(session_id):
    """GET /api/chat/sessions/{id}/messages -> 转为 [(user, bot)]"""
    ...

def stream_chat(session_id, user_message, history):
    """流式生成器：yield 更新后的 history"""
    ...
```

> ✅ 注意：`stream_chat` 必须是 **generator**，且配合 `.queue()`

---

### 🔹 步骤 5：绑定事件 & 启用队列

在 `chat.py` 中完成事件绑定：

```python
# 在 render() 末尾
components = { ... }  # 上一步返回的控件字典

# 状态
session_id_state = gr.State(None)
chat_history_state = gr.State([])

# 事件
components["new_session_btn"].click(
    chat_handler.create_new_session,
    inputs=[],
    outputs=[
        components["session_dropdown"],
        session_id_state,
        chat_history_state,
        components["chatbot"]
    ]
)

components["send_btn"].click(
    chat_handler.stream_chat,
    inputs=[session_id_state, components["msg_input"], chat_history_state],
    outputs=[chat_history_state, components["chatbot"]],
    queue=True  # 👈 关键
).then(lambda: "", None, components["msg_input"])
```

并在 `app.py` 中启用队列：
```python
demo = create_gradio_interface().queue(max_size=10)
```

---

## 📅 下一步行动

我建议我们按以下顺序执行：

1. **你确认此方案可行**
2. 我为你生成：
   - ✅ 完整的 `main_layout.py`
   - ✅ 四个页面的占位 `render()` 函数
   - ✅ `chat.py` 的完整 UI 布局（含控件引用）
3. 你创建对应文件
4. 我再提供 `chat_handler.py` 的完整实现（对接你的 API）

---

✅ **请回复：“确认，开始生成 UI 框架代码”**，我将立即输出第一步所需的所有文件内容。