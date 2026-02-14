# frontend/ui/pages/chat_ui.py
import gradio as gr

from frontend.handlers.chat_handler import (
    load_session_list,
    load_messages,
    chat_turn,
)
from frontend.handlers.llm_setting_handler import build_choices_from_configs

def render(llm_configs_state=None, default_id_state=None):
    """聊天页面：会话管理 + 对话交互（含完整事件绑定）"""

    # --- 辅助函数（数据/事件逻辑） ---
    def _load_messages(session_id, cache):
        """优先从缓存获取历史，未命中再请求后端"""
        if not session_id:
            return cache, []
        if session_id in cache:
            return cache, cache[session_id]
        history = load_messages(session_id)
        updated_cache = dict(cache)
        updated_cache[session_id] = history
        return updated_cache, history

    def _append_user_message(session_id, user_message, cache):
        """先乐观写入用户消息到缓存与 Chatbot"""
        if not user_message:
            return cache, cache.get(session_id, [])
        history = list(cache.get(session_id, []))
        history.append({"role": "user", "content": user_message, "_pending": True})
        updated_cache = dict(cache)
        updated_cache[session_id] = history
        return updated_cache, history

    def _send_message(session_id, user_message, cache, config_id):
        """发送消息（非流式）并写入缓存"""
        if not user_message:
            return cache, cache.get(session_id, [])
        history = chat_turn(
            session_id,
            user_message,
            [m for m in cache.get(session_id, []) if not (isinstance(m, dict) and m.get("_pending"))],
            config_id,
        )
        updated_cache = dict(cache)
        updated_cache[session_id] = history
        return updated_cache, history

    def _new_chat():
        """新建会话：重置会话ID、输入框、聊天记录"""
        return None, "", gr.update(value=[])

    # --- 初始值获取与状态管理 ---
    initial_configs = llm_configs_state.value if llm_configs_state else []
    initial_default_id = default_id_state.value if default_id_state else None
    initial_choices = build_choices_from_configs(initial_configs, initial_default_id)
    nav_items = load_session_list()

    session_id_state = gr.State(None)
    chat_history_state = gr.State({})
    if llm_configs_state is None:
        llm_configs_state = gr.State(value=[])
    if default_id_state is None:
        default_id_state = gr.State(value=None)

    # --- UI 布局 ---
    with gr.Row():
        # 左侧：会话控制面板
        with gr.Column(scale=1, min_width=200, elem_classes="sidebar"):
            new_chat_btn = gr.Button("➕ 新对话", variant="primary")
            gr.Markdown("#### 最近对话")
            nav_buttons = []
            for title, sid in nav_items:
                btn = gr.Button(title, elem_classes="nav-item")
                nav_buttons.append((btn, sid))

        # 右侧：聊天区域
        with gr.Column(scale=7):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 💬 聊天")
                with gr.Column(scale=3):
                    pass
                with gr.Column(scale=1):
                    current_model_dropdown = gr.Dropdown(
                        label="当前模型",
                        choices=initial_choices,
                        value=initial_default_id,
                        interactive=True,
                        allow_custom_value=False,
                    )
            chatbot = gr.Chatbot(elem_id="chat_display", height=500, label="对话历史")
            with gr.Row():
                msg_input = gr.Textbox(
                    placeholder="请输入您的问题，按回车或点击发送...",
                    lines=1,
                    scale=7,
                    buttons=["copy"],
                    submit_btn="发送",
                )

    # --- 控件绑定（集中注册） ---
    new_chat_btn.click(
        _new_chat,
        inputs=[],
        outputs=[session_id_state, msg_input, chatbot],
    )

    for btn, sid in nav_buttons:
        btn.click(
            lambda s=sid: s,
            inputs=[],
            outputs=[session_id_state],
        ).then(
            _load_messages,
            inputs=[session_id_state, chat_history_state],
            outputs=[chat_history_state, chatbot],
        )

    msg_input.submit(
        _append_user_message,
        inputs=[session_id_state, msg_input, chat_history_state],
        outputs=[chat_history_state, chatbot],
    ).then(
        _send_message,
        inputs=[session_id_state, msg_input, chat_history_state, default_id_state],
        outputs=[chat_history_state, chatbot],
    ).then(
        lambda: "",
        None,
        msg_input
    )

    return current_model_dropdown

