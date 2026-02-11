# frontend/ui/pages/chat_ui.py
import gradio as gr

from frontend.handlers.chat_handler import (
    load_session_list,
    create_new_session,
    load_messages,
    chat_turn  # ← 改为 chat_turn（非流式）
)
from frontend.handlers.llm_setting_handler import build_choices_from_configs

def render(llm_configs_state=None, default_id_state=None):
    """聊天页面：会话管理 + 对话交互（含完整事件绑定）"""
    
    # --- 辅助函数（数据/事件逻辑） ---
    def _resolve_default_model_info(configs, default_id):
        """从配置列表中解析默认模型信息"""
        for cfg in configs or []:
            if str(cfg.get("id")) == str(default_id):
                model = cfg.get("model_name") or "—"
                provider = cfg.get("provider") or "—"
                return model, provider
        return "—", "—"
    
    def _load_sessions():
        """加载历史会话列表"""
        sessions = load_session_list()
        return gr.update(choices=sessions)

    # 获取初始值用于下拉框
    initial_configs = llm_configs_state.value if llm_configs_state else []
    initial_default_id = default_id_state.value if default_id_state else None
    initial_choices = build_choices_from_configs(initial_configs, initial_default_id)

    # --- UI 布局 ---
    with gr.Row():
        # 左侧：会话控制面板
        with gr.Column(scale=1, min_width=180):
            gr.Markdown("### 💬 会话")
            session_dropdown = gr.Dropdown(
                label="历史会话",
                choices=[],  # 初始为空，由 .load() 填充
                interactive=True,
                value=None
            )
            # delete_session_btn = gr.Button("🗑️ 删除会话", variant="stop", size="sm")

        # 右侧：聊天区域
        with gr.Column(scale=7):
            with gr.Row():
                with gr.Column(scale=1):
                    gr.Markdown("### 💬 聊天")
                with gr.Column(scale=3):
                    pass # 占位，保持布局   
                with gr.Column(scale=1):
                    current_model_dropdown = gr.Dropdown(
                        label="当前模型",
                        choices=initial_choices,
                        value=initial_default_id,
                        interactive=True,
                        allow_custom_value=False,
                    )
            
            chatbot = gr.Chatbot(
                elem_id="chat_display",
                height=500,
                label="对话历史",
                type="messages",
            )
            with gr.Row():
                msg_input = gr.Textbox(
                    placeholder="请输入您的问题，按回车或点击发送...",
                    lines=1,
                    scale=7
                )
                send_btn = gr.Button("📤 发送", variant="primary", scale=1)
                # clear_btn = gr.Button("🧹 清空", scale=1)

    # 状态管理
    session_id_state = gr.State(None)
    chat_history_state = gr.State([])
    if llm_configs_state is None:
        llm_configs_state = gr.State(value=[])
    if default_id_state is None:
        default_id_state = gr.State(value=None)

    # --- 控件绑定（集中注册） ---
    # 1. 切换会话
    session_dropdown.change(
        load_messages,
        inputs=[session_dropdown],
        outputs=[chat_history_state, chatbot],
        show_progress="minimal"
    ).then(
        lambda sid: sid,
        inputs=[session_dropdown],
        outputs=[session_id_state]
    )

    # 2. 发送消息（非流式，完整响应）
    send_event = send_btn.click(
        chat_turn,
        inputs=[session_id_state, msg_input, chat_history_state],
        outputs=[chatbot],
        show_progress="minimal"
    ).then(
        lambda: "", None, msg_input
    ).then(
        lambda hist: hist, [chatbot], chat_history_state
    )

    # 3. 回车发送（非流式，完整响应）
    msg_input.submit(
        chat_turn,
        inputs=[session_id_state, msg_input, chat_history_state],
        outputs=[chatbot],
        show_progress="minimal"
    ).then(
        lambda: "", None, msg_input
    ).then(
        lambda hist: hist, [chatbot], chat_history_state
    )

    # 页面首次加载时获取会话列表
    # 注意：需要在 .load() 中引用组件，无法在组件定义前添加
    
    return current_model_dropdown

