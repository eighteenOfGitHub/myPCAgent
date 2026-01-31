# frontend/ui/pages/preference_setting_ui.py
import gradio as gr
from frontend.handlers.preference_setting_handler import (
    fetch_llm_basic_options,
    fetch_default_llm_config_id,
    set_default_llm_config,
)

def create_preference_setting_ui(visible: bool = True):
    """Create preference settings UI container."""
    def _mark_default_choice(choices, default_id):
        if not default_id:
            return choices
        marked = []
        for label, value in choices:
            if value == default_id:
                label = f"{label}(default model)"
            marked.append((label, value))
        return marked

    def _load_initial():
        choices = fetch_llm_basic_options() or []
        default_id = fetch_default_llm_config_id()
        if default_id is None:
            choices = [("", None)] + choices
            selected = None
        else:
            choices = _mark_default_choice(choices, default_id)
            selected = (
                default_id
                if any(c[1] == default_id for c in choices)
                else (choices[0][1] if choices else None)
            )
        return choices, selected

    initial_choices, initial_value = _load_initial()

    with gr.Column(visible=visible) as preference_ui:
        gr.Markdown("## 🧠 Default LLM Model")
        default_llm_dropdown = gr.Dropdown(
            choices=initial_choices,
            value=initial_value,
            interactive=True,
            allow_custom_value=False,
        )
        with gr.Row():
            refresh_btn = gr.Button("🔄 Refresh", variant="secondary", scale=1)
            save_btn = gr.Button("💾 Save Default", scale=1)
        status_text = gr.Textbox(value="", show_label=False, interactive=False, visible=False)
        status_timer = gr.Timer(3.0, active=False)

        def _hide_status():
            return (
                gr.update(value="", visible=False),
                gr.update(active=False),
            )

        def on_refresh(current_id):
            choices, selected = _load_initial()
            if selected is None and current_id is not None and any(c[1] == current_id for c in choices):
                selected = current_id
            return (
                gr.update(choices=choices, value=selected),
                gr.update(value="✅ Refreshed.", visible=True),
                gr.update(active=True),
            )

        def on_save(default_llm_id):
            success, msg, _ = set_default_llm_config(default_llm_id)
            if not success:
                return (
                    gr.update(),
                    gr.update(value=f"❌ {msg}", visible=True),
                    gr.update(active=True),
                )
            choices, selected = _load_initial()
            return (
                gr.update(choices=choices, value=selected),
                gr.update(value="✅ Saved default model.", visible=True),
                gr.update(active=True),
            )

        refresh_btn.click(
            fn=on_refresh,
            inputs=default_llm_dropdown,
            outputs=[default_llm_dropdown, status_text, status_timer],
        )
        save_btn.click(
            fn=on_save,
            inputs=default_llm_dropdown,
            outputs=[default_llm_dropdown, status_text, status_timer],
        )
        status_timer.tick(fn=_hide_status, inputs=[], outputs=[status_text, status_timer])

    return preference_ui