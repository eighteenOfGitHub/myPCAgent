# frontend/ui/pages/chat_ui.py
import gradio as gr

from frontend.handlers.chat_handler import (
    load_session_list,
    load_messages,
    chat_turn,
    ensure_session,
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

    def _append_user_message(session_id, user_message, cache, user_input_state):
        """先乐观写入用户消息到缓存与 Chatbot，同时记录输入状态"""
        if not user_message:
            return cache, cache.get(session_id, []), user_input_state
        history = list(cache.get(session_id, []))
        history.append({"role": "user", "content": user_message, "_pending": True})
        updated_cache = dict(cache)
        updated_cache[session_id] = history
        return updated_cache, history, user_message

    def _send_message(session_id, user_message, cache, config_id):
        """发送消息（非流式）并写入缓存"""
        if not user_message or not session_id:
            return cache, cache.get(session_id, []) if session_id else []
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
        return None, "", gr.update(value=[]), ""

    def _ensure_session_and_refresh(session_id, user_message):
        """确保会话ID并刷新左侧列表"""
        new_sid = ensure_session(session_id, user_message)
        return new_sid, load_session_list()

    def _sync_nav_buttons(nav_items):
        """根据 nav_items 状态更新按钮文本/显示"""
        updates = []
        for idx in range(MAX_NAV_BUTTONS):
            if idx < len(nav_items):
                title, _sid = nav_items[idx]
                updates.append(gr.update(value=title, visible=True))
            else:
                updates.append(gr.update(visible=False))
        return updates

    MAX_NAV_BUTTONS = 20

    # --- 初始值获取与状态管理 ---
    initial_configs = llm_configs_state.value if llm_configs_state else []
    initial_default_id = default_id_state.value if default_id_state else None
    initial_choices = build_choices_from_configs(initial_configs, initial_default_id)
    nav_items = load_session_list()

    session_id_state = gr.State(None)
    chat_history_state = gr.State({})
    nav_items_state = gr.State(nav_items)
    if llm_configs_state is None:
        llm_configs_state = gr.State(value=[])
    if default_id_state is None:
        default_id_state = gr.State(value=None)
    user_input_state = gr.State("")

    # --- UI 布局 ---
    with gr.Row():
        # 左侧：会话控制面板
        with gr.Column(scale=1, min_width=200, elem_classes="sidebar"):
            new_chat_btn = gr.Button("➕ 新对话", variant="primary")
            gr.Markdown("#### 最近对话")
            nav_buttons = []
            for idx in range(MAX_NAV_BUTTONS):
                btn = gr.Button(
                    value=nav_items[idx][0] if idx < len(nav_items) else "",
                    visible=idx < len(nav_items),
                    elem_classes="nav-item",
                )
                nav_buttons.append(btn)

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
        outputs=[session_id_state, msg_input, chatbot, user_input_state],
    )

    for idx, btn in enumerate(nav_buttons):
        btn.click(
            lambda items, i=idx: items[i][1] if len(items) > i else None,
            inputs=[nav_items_state],
            outputs=[session_id_state],
        ).then(
            _load_messages,
            inputs=[session_id_state, chat_history_state],
            outputs=[chat_history_state, chatbot],
        )

    nav_items_state.change(
        _sync_nav_buttons,
        inputs=[nav_items_state],
        outputs=nav_buttons,
    )

    msg_input.submit(
        _append_user_message,
        inputs=[session_id_state, msg_input, chat_history_state, user_input_state],
        outputs=[chat_history_state, chatbot, user_input_state],
    ).then(
        lambda: "",
        None,
        msg_input
    ).then(
        _ensure_session_and_refresh,
        inputs=[session_id_state, user_input_state],
        outputs=[session_id_state, nav_items_state],
    ).then(
        _sync_nav_buttons,
        inputs=[nav_items_state],
        outputs=nav_buttons,
    ).then(
        _send_message,
        inputs=[session_id_state, user_input_state, chat_history_state, default_id_state],
        outputs=[chat_history_state, chatbot],
    )

    return current_model_dropdown

