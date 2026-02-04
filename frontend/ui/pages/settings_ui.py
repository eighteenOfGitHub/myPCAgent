# frontend/ui/pages/settings_ui.py
import gradio as gr
from .default_setting_ui import create_default_setting_ui
from .llm_setting_ui import create_llm_models_setting_ui



def render():
    with gr.Row():
        # 左侧菜单栏
        with gr.Column(scale=1, min_width=150):
            general_btn = gr.Button("General")
            llm_btn = gr.Button("LLM Models")

        # 右侧内容区
        with gr.Column(scale=7):
            preference_ui = create_default_setting_ui(visible=True)
            llm_ui, llm_config_df = create_llm_models_setting_ui(visible=False)

            # 切换逻辑：控制可见性
            def show_general():
                return gr.update(visible=True), gr.update(visible=False)

            def show_llm():
                return gr.update(visible=False), gr.update(visible=True)

            general_btn.click(show_general, outputs=[preference_ui, llm_ui])
            llm_btn.click(show_llm, outputs=[preference_ui, llm_ui])

    return [general_btn, llm_btn, preference_ui, llm_ui, llm_config_df]