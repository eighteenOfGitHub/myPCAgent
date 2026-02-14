# 前端服务（Gradio）开发规范与流程速查手册

适用范围：frontend/ 目录的 Gradio 前端代码（app.py、handlers、ui/pages）。

一、核心原则
- 分层清晰：辅助函数（数据/事件逻辑）→ UI 布局 → 控件绑定（事件注册）分离。
- 只读表格：管理类列表默认只读（interactive=False），允许选择复制文本。
- 与后端对齐：请求/响应使用 shared 下的模型约定，避免前端硬编码字段名错误。
- 安全优先：密钥不落盘不回显；日志不打印敏感信息；遵循 FERNET 加密流转。
- 可维护：命名清晰、注释分段、样式最小化、组件按区域分组。

二、目录与文件组织
- frontend/app.py：应用入口，聚合页面。
- frontend/handlers/*.py：与后端交互与业务逻辑封装（HTTP 调用、数据整理）。
- frontend/ui/pages/*.py：页面函数（返回 UI 容器与关键控件）。
- shared/*.py：与后端共享的请求/响应/枚举类型定义（前端只依赖这些类型约定）。

三、页面范式（推荐骨架）
- 组织顺序：1) 辅助函数 2) 初始值获取与状态管理 3) UI 布局 4) 控件绑定

```python
# --- 辅助函数（数据/事件逻辑） ---
def _initial_rows(): ...
def _on_change(...): ...
def _on_submit(...): ...
def _refresh(): ...

# --- 初始值获取与状态管理 ---
initial_rows = _initial_rows()
selection_state = gr.State(None)

# --- UI 布局 ---
with gr.Column(visible=True) as root:
    # 标题与操作同行：左文右钮
    with gr.Row():
        with gr.Column(scale=8):
            gr.Markdown("### 标题")
        with gr.Column(scale=2, min_width=120):
            refresh_btn = gr.Button("🔄 刷新", variant="secondary")

    # 表格只读，可复制
    df = gr.Dataframe(
        headers=[...],
        datatype=[...],
        interactive=False,
        wrap=True,
        elem_id="table_id",
        value=initial_rows,
        type="array",
    )
    gr.HTML("""
    <style>
    #table_id table, #table_id table * { user-select: text !important; -webkit-user-select: text !important; }
    </style>
    """)

# --- 控件绑定（集中注册） ---
refresh_btn.click(fn=_refresh, inputs=[], outputs=[df])
```

四、布局规范
- 标题与操作按钮同行：gr.Row + 两列（左 Markdown，右 Button）。
- 列宽控制：优先使用 scale（如 8:2）+ min_width 控制按钮列。
- 表单区域使用 Accordion 折叠，按钮置于右侧窄列。

五、表格（gr.Dataframe）规范
- 默认只读：interactive=False。
- 复制文本：通过 elem_id 注入 CSS，开启 user-select。
- 长文本：wrap=True，避免撑破布局。
- 数据类型：datatype 与 headers 对齐，使用 "str"、"number"、"bool"、"date" 等。
- 值格式：type="array" 与后端列表兼容；刷新回写使用 gr.update(value=rows)。
- 可选交互：
  - row_selectable=True / col_selectable=True：如需行/列选择事件。
  - height / max_rows：控制显示高度或最大行数。

六、事件与网络交互
- 事件绑定统一放在函数末尾，避免穿插 UI。
- 网络请求封装到 frontend/handlers，页面只调用 handler 方法：
  - 例如：handlers.llm_setting.get_all_llm_configs() / submit_new_llm_config(...)
- 返回值约定：handler 返回 (success: bool, data_or_error: Any)。
- 异常处理：页面层不抛异常，降级为空数据 + 控制台警告；必要时在 UI 显示提示文本。

### 6.1 API 路由统一获取（重要）
- **来源唯一**：所有 handler 必须从 `config.env_config.env_config` 获取 `API_BASE_URL`，避免硬编码 URL。
- **初始化方式**：在 handler 模块顶部声明：
  ```python
  from config.env_config import env_config
  
  # 重要过程：从 env_config 统一获取 API 基址
  API_BASE = env_config.API_BASE_URL
  ```
- **使用方式**：所有请求使用 `f"{API_BASE}/endpoint"` 格式。
- **环境切换**：若需切换 API 地址（开发/生产），仅在 `config/env_config.yaml` 修改 `API_BASE_URL` 字段，无需改动代码。
- **示例**：
  ```python
  # ❌ 错误：硬编码
  response = requests.get("http://localhost:8000/api/settings/llm/")
  
  # ✅ 正确：动态获取
  response = requests.get(f"{API_BASE}/settings/llm/")
  ```

七、状态管理
- 临时态：gr.State 存放当前选择或分页偏移等页面状态。
- 会话态：谨慎使用全局变量；优先以显式输入输出传递。
- 不在前端保存敏感信息（如 api_key），输入只用于提交。

八、安全与合规
- 密钥输入：type="password"，不在前端回显与日志输出。
- 加密流转：提交前端调用 shared/crypto 的 Fernet 加密（前后端同钥），后端解密后存密文。
- 日志：避免打印 headers、body 中的敏感字段。
- CORS：按 config/env_config.yaml 配置的白名单来源访问。

九、性能建议
- 减少不必要刷新：刷新按钮触发，或在成功提交后精准更新数据。
- 文本大字段：wrap + 固定高度，避免页面抖动。
- 事件防抖：输入框联动逻辑可使用即时校验，尽量避免频繁请求。

十、可测试性
- handler 函数纯粹：入参输出明确，便于单测或 mock http。
- 页面函数返回关键控件（如 df/按钮），便于在集成测试中触发交互。
- 约定返回数据结构（headers、字段名）与 shared 模型一一对应。

十一、示例片段（只读可复制 Dataframe 与刷新）
```python
# --- 辅助函数（数据/事件逻辑） ---
def _refresh():
    ok, data = handlers.llm_setting.get_all_llm_configs()
    if ok and isinstance(data, list):
        rows = [[d.get("id"), d.get("provider"), d.get("model_name"),
                 d.get("base_url"), d.get("created_at"), d.get("updated_at")] for d in data]
        return gr.update(value=rows)
    return gr.update(value=[])

# --- UI 布局 ---
df = gr.Dataframe(
    headers=["ID", "Provider", "Model", "Base URL", "Created At", "Updated At"],
    datatype=["number", "str", "str", "str", "str", "str"],
    interactive=False,
    wrap=True,
    elem_id="llm_config_table",
    value=_initial_rows(),
    type="array",
)

# --- 控件绑定（集中注册） ---
refresh_btn.click(fn=_refresh, inputs=[], outputs=[df])
```

十二、命名与注释
- 事件函数：on_submit / _on_provider_change / refresh_xxx。
- UI 分段注释：-- 添加区域、-- 管理区域、-- 表格区域。
- 控件命名：provider、model_name、api_key、base_url、submit_btn、refresh_btn、llm_config_df。

十三、提交前检查清单（Checklist）
- 分层是否清晰（辅助函数 / UI / 绑定）？
- Dataframe 是否只读且可复制（interactive=False + CSS）？
- 与后端字段是否一致（headers/keys 对齐 shared 模型）？
- 是否避免打印敏感信息？
- 刷新逻辑是否健壮（失败降级为空列表）？
- API 路由是否统一获取（来源 env_config，无硬编码）?