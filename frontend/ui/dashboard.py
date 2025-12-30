# frontend/ui/dashboard.py
import gradio as gr
from frontend.handers.dashboard import update_chat_with_hello

def create_gradio_interface():
    with gr.Blocks(title="LangGraph Dashboard") as demo:
        # 定义状态变量，用于存储聊天历史
        chat_history = gr.State([])

        with gr.Row():
            with gr.Column(scale=1):
                # 左侧栏
                gr.Markdown("## 控制面板")
                hello_btn = gr.Button("Say Hello to Backend") # 添加按钮
            with gr.Column(scale=4):
                # 右侧栏
                gr.Markdown("## 聊天")
                chatbot = gr.Chatbot(
                    height=500,
                    elem_id="chat_display"
                )

        # 修改：同时更新 chatbot 和 chat_history State
        hello_btn.click(
            fn=update_chat_with_hello,
            inputs=[chat_history],           # 传入当前的 chat_history State
            outputs=[chat_history, chatbot], # 同时更新 State 和 chatbot
            show_progress=True
        )

    return demo