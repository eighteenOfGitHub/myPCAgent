# frontend/ui/pages/general_setting.py
import gradio as gr


def create_general_setting_ui(visible=True):
    with gr.Column(visible=visible) as general_ui:
        gr.Markdown("### Default LLM Model")
        
        # 使用模拟数据填充下拉框
        mock_choices = [
            ("OpenAI / gpt-4o", 1),
            ("Anthropic / claude-3-5-sonnet", 2),
            ("Ollama / llama3", 3)
        ]
        
        default_llm_dropdown = gr.Dropdown(
            choices=mock_choices,
            label="Default LLM",
            value=1,  # 默认选中第一个
            interactive=True
        )
        
        save_btn = gr.Button("Save Default")
        status_text = gr.Textbox(value="", show_label=False, interactive=False, visible=False)

        # 模拟保存逻辑（无实际 API 调用）
        def on_save(default_llm_id):
            if default_llm_id is None:
                return gr.update(value="Please select a model", visible=True)
            return gr.update(value="Saved!", visible=True)

        save_btn.click(
            fn=on_save,
            inputs=default_llm_dropdown,
            outputs=status_text
        )

    return general_ui