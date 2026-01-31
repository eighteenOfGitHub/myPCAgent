# frontend/ui/pages/preference_setting_ui.py
import gradio as gr

def create_preference_setting_ui(visible: bool = True):
    """Create preference settings UI container."""
    with gr.Column(visible=visible) as preference_ui:
        gr.Markdown("## ℹ️ Preference Settings")
    return preference_ui