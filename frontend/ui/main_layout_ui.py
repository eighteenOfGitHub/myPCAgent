# frontend/ui/main_layout_ui.py
import gradio as gr
from frontend.ui.pages import dashboard, chat, agent, settings
from frontend.handlers.chat_handler import load_session_list

def create_gradio_interface():
    """
    创建主 Gradio 界面，使用 Tabs 组织多页面
    """
    with gr.Blocks(title="PC Agent") as demo:
        with gr.Tabs():
            with gr.Tab("🏠 Dashboard"):
                dashboard()
            
            with gr.Tab("💬 Chat"):
                session_dropdown = chat()
            
            with gr.Tab("🤖 Agent"):
                agent()
            
            with gr.Tab("⚙️ Settings"):
                settings()


        demo.load(
            fn=lambda: gr.Dropdown(choices=load_session_list()),
            inputs=None,
            outputs=session_dropdown,
            show_progress="hidden"
        )
    
    return demo