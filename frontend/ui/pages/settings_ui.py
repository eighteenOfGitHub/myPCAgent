# frontend/ui/pages/settings_ui.py
import gradio as gr
from .default_setting_ui import create_default_setting_ui
from .llm_setting_ui import create_llm_models_setting_ui

def render(llm_configs_state=None, default_id_state=None):
    
    # --- 辅助函数（数据/事件逻辑） ---
    def show_general():
        """切换到通用设置"""
        return gr.update(visible=True), gr.update(visible=False)

    def show_llm():
        """切换到 LLM 模型设置"""
        return gr.update(visible=False), gr.update(visible=True)
    
    # --- UI 布局 ---
    with gr.Row():
        # 左侧菜单栏
        with gr.Column(scale=1, min_width=150):
            general_btn = gr.Button("General")
            llm_btn = gr.Button("LLM Models")

        # 右侧内容区
        with gr.Column(scale=7):
            preference_ui = create_default_setting_ui(visible=True)
            llm_ui, llm_config_df, shared_configs, shared_default = create_llm_models_setting_ui(
                visible=False,
                llm_configs_state=llm_configs_state,
                default_id_state=default_id_state
            )

    # --- 控件绑定（集中注册） ---
    general_btn.click(show_general, outputs=[preference_ui, llm_ui])
    llm_btn.click(show_llm, outputs=[preference_ui, llm_ui])

    return [general_btn, llm_btn, preference_ui, llm_ui, llm_config_df, shared_configs, shared_default]