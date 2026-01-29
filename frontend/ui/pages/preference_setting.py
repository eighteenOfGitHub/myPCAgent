# frontend/ui/pages/preference_setting.py
import gradio as gr
from frontend.handlers.preference_setting import (
    fetch_llm_basic_options,
    fetch_default_llm_config_id,
    set_default_llm_config,
)

def create_preference_setting_ui(visible: bool = True):
    def _load_initial():
        choices = fetch_llm_basic_options() or []
        default_id = fetch_default_llm_config_id()
        if default_id is None:
            choices = [("", None)] + choices
            selected = None
        else:
            selected = (
                default_id
                if any(c[1] == default_id for c in choices)
                else (choices[0][1] if choices else None)
            )
        return choices, selected

    initial_choices, initial_value = _load_initial()

    with gr.Column(visible=visible) as preference_ui:
        gr.Markdown("### Default LLM Model")
        default_llm_dropdown = gr.Dropdown(
            choices=initial_choices,
            label="Default LLM",
            value=initial_value,
            interactive=True,
            allow_custom_value=False,
        )
        refresh_btn = gr.Button("Refresh Models", variant="secondary")
        save_btn = gr.Button("Save Default")
        status_text = gr.Textbox(value="", show_label=False, interactive=False, visible=False)

        def on_refresh(current_id):
            choices, selected = _load_initial()
            if selected is None and current_id is not None and any(c[1] == current_id for c in choices):
                selected = current_id
            return gr.update(choices=choices, value=selected)

        def on_save(default_llm_id):
            success, msg, _ = set_default_llm_config(default_llm_id)
            if not success:
                return gr.update(value=f"❌ {msg}", visible=True)
            return gr.update(value="✅ Saved default model.", visible=True)

        refresh_btn.click(fn=on_refresh, inputs=default_llm_dropdown, outputs=default_llm_dropdown)
        save_btn.click(fn=on_save, inputs=default_llm_dropdown, outputs=status_text)

    return preference_ui