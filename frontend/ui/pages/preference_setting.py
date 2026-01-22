# frontend/ui/pages/preference_setting.py
import gradio as gr
from frontend.handlers.preference_setting import (
    fetch_llm_basic_options,
    fetch_default_llm_config_id,
    set_default_llm_config,
)

def create_preference_setting_ui(visible: bool = True):
    initial_choices = fetch_llm_basic_options() or []
    default_id = fetch_default_llm_config_id()
    if default_id is None:
        # 后端无默认值时，列表首元素为空项
        initial_choices = [("", None)] + initial_choices
        initial_value = None
    else:
        initial_value = (
            default_id
            if any(c[1] == default_id for c in initial_choices)
            else (initial_choices[0][1] if initial_choices else None)
        )

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
            choices = fetch_llm_basic_options() or []
            backend_default = fetch_default_llm_config_id()
            if backend_default is None:
                # 无默认值 → 列表首元素为空项，并默认选中 None
                choices = [("", None)] + choices
                selected = current_id if any(c[1] == current_id for c in choices) else None
            else:
                if any(c[1] == backend_default for c in choices):
                    selected = backend_default
                elif current_id is not None and any(c[1] == current_id for c in choices):
                    selected = current_id
                else:
                    selected = choices[0][1] if choices else None
            return gr.update(choices=choices, value=selected)

        def on_save(default_llm_id):
            success, msg, _ = set_default_llm_config(default_llm_id)
            if not success:
                return gr.update(value=f"❌ {msg}", visible=True)
            return gr.update(value="✅ Saved default model.", visible=True)

        refresh_btn.click(fn=on_refresh, inputs=default_llm_dropdown, outputs=default_llm_dropdown)
        save_btn.click(fn=on_save, inputs=default_llm_dropdown, outputs=status_text)

    return preference_ui