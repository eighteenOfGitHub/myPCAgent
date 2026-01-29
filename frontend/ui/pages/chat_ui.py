# frontend/ui/pages/chat_ui.py
import gradio as gr

from frontend.handlers.chat_handler import (
    load_session_list,
    create_new_session,
    load_messages,
    stream_chat
)

def render():
    """聊天页面：会话管理 + 对话交互（含完整事件绑定）"""
    with gr.Row():
        # 左侧：会话控制面板
        with gr.Column(scale=1, min_width=180):
            gr.Markdown("### 💬 会话管理")
            session_dropdown = gr.Dropdown(
                label="历史会话",
                choices=[],
                interactive=True,
                value=None
            )
            new_session_btn = gr.Button("🆕 新建会话", variant="primary", size="sm")
            delete_session_btn = gr.Button("🗑️ 删除会话", variant="stop", size="sm")
            
            gr.Markdown("### ⚙️ 当前配置")
            model_info = gr.Textbox(
                label="模型",
                value="未选择会话",
                interactive=False
            )
            provider_info = gr.Textbox(
                label="提供商",
                value="—",
                interactive=False
            )

        # 右侧：聊天区域
        with gr.Column(scale=3):
            chatbot = gr.Chatbot(
                elem_id="chat_display",
                height=500,
                label="对话历史",
            )
            msg_input = gr.Textbox(
                label="输入消息",
                placeholder="请输入您的问题，按回车或点击发送...",
                lines=1
            )
            with gr.Row():
                send_btn = gr.Button("📤 发送", variant="primary")
                clear_btn = gr.Button("🧹 清空")

    # 状态管理
    session_id_state = gr.State(None)
    chat_history_state = gr.State([])

    # 事件绑定
    # 1. 新建会话
    new_session_btn.click(
        create_new_session,
        inputs=[],
        outputs=[
            session_dropdown,
            session_id_state,
            chat_history_state,
            chatbot
        ],
        show_progress="minimal"
    )

    # 2. 切换会话
    session_dropdown.change(
        load_messages,
        inputs=[session_dropdown],
        outputs=[chat_history_state, chatbot],
        show_progress="minimal"
    ).then(
        lambda sid: (sid, "未加载", "—") if not sid else (sid, f"会话 {sid}", "openai"),
        inputs=[session_dropdown],
        outputs=[session_id_state, model_info, provider_info]
    )

    # 3. 发送消息（流式）
    send_event = send_btn.click(
        stream_chat,
        inputs=[session_id_state, msg_input, chat_history_state],
        outputs=[chatbot],
        queue=True,
        show_progress="minimal"
    ).then(
        lambda: "", None, msg_input  # 清空输入框
    ).then(
        lambda hist: hist, [chatbot], chat_history_state  # 同步状态
    )

    # 4. 回车发送
    msg_input.submit(
        stream_chat,
        inputs=[session_id_state, msg_input, chat_history_state],
        outputs=[chatbot],
        queue=True,
        show_progress="minimal"
    ).then(
        lambda: "", None, msg_input
    ).then(
        lambda hist: hist, [chatbot], chat_history_state
    )

    return session_dropdown

