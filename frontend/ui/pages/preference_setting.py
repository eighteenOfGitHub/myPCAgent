# frontend/ui/pages/preference_setting.py
import gradio as gr
from frontend.handlers.preference_setting import fetch_llm_basic_options



def create_preference_setting_ui(visible: bool = True):
    initial_choices = fetch_llm_basic_options()
    initial_value = initial_choices[0][1] if initial_choices else None

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
            choices = fetch_llm_basic_options()
            selected = current_id if any(c[1] == current_id for c in choices) else (choices[0][1] if choices else None)
            return gr.update(choices=choices, value=selected)

        def on_save(default_llm_id):
            if default_llm_id is None:
                return gr.update(value="Please select a model", visible=True)
            return gr.update(value="Saved locally (TODO: persist via API)", visible=True)

        refresh_btn.click(
            fn=on_refresh,
            inputs=default_llm_dropdown,
            outputs=default_llm_dropdown,
        )

        save_btn.click(
            fn=on_save,
            inputs=default_llm_dropdown,
            outputs=status_text,
        )

    return preference_ui