# frontend/ui/pages/default_setting_ui.py
import gradio as gr

def create_default_setting_ui(visible: bool = True):
    """Create default settings UI container."""
    with gr.Column(visible=visible) as default_setting_ui:
        gr.Markdown("## ℹ️ Default Settings")
    return default_setting_ui