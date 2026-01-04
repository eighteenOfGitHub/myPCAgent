# frontend/ui/pages/settings.py
import gradio as gr
from .general_setting import create_general_setting_ui
from .llm_setting import create_llm_models_setting_ui



def render():
    with gr.Row():
        # 左侧菜单栏
        with gr.Column(scale=1, min_width=150):
            general_btn = gr.Button("General")
            llm_btn = gr.Button("LLM Models")

        # 右侧内容区
        with gr.Column(scale=3):
            general_ui = create_general_setting_ui(visible=True)
            llm_ui = create_llm_models_setting_ui(visible=False)

    # 切换逻辑：控制可见性
    def show_general():
        return gr.update(visible=True), gr.update(visible=False)

    def show_llm():
        return gr.update(visible=False), gr.update(visible=True)

    general_btn.click(show_general, outputs=[general_ui, llm_ui])
    llm_btn.click(show_llm, outputs=[general_ui, llm_ui])

    return [general_btn, llm_btn, general_ui, llm_ui]