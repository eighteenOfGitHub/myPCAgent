# frontend/ui/pages/llm_models_setting.py

import gradio as gr


def create_llm_models_setting_ui(visible=True):
    with gr.Column(visible=visible) as llm_ui:
        gr.Markdown("### 🔧 Manage LLM Models")

        # ===== 添加区域 =====
        with gr.Accordion("➕ Add New LLM", open=False):
            provider = gr.Dropdown(
                choices=["OpenAI", "Ollama"],
                label="Provider",
                interactive=True,
                value=None
            )
            model_name = gr.Textbox(label="Model Name", placeholder="e.g., gpt-4o, llama3")
            api_key = gr.Textbox(label="API Key", type="password")
            base_url = gr.Textbox(
                label="Base URL (Optional)",
                placeholder="e.g., http://localhost:11434 for Ollama"
            )

            # Submit 按钮右下角
            with gr.Row():
                gr.Column(scale=8)
                with gr.Column(scale=2, min_width=120):
                    submit_btn = gr.Button("✅ Submit", variant="primary", size="sm")

        # ===== 管理区域 =====
        gr.Markdown("### 📋 Existing LLM Configurations")

        mock_configs = [
            {"id": 1, "provider": "OpenAI", "model": "gpt-4o", "api_key": "sk-****1234", "status": "✅ Ready"},
            {"id": 2, "provider": "Ollama", "model": "llama3", "api_key": "N/A", "status": "⚠️ Not tested"}
        ]

        status_textboxes = []

        with gr.Column(variant="panel"):
            for cfg in mock_configs:
                with gr.Row():
                    gr.Textbox(value=cfg['provider'], interactive=False, min_width=80, container=False, show_label=False)
                    gr.Textbox(value=cfg['model'], interactive=False, min_width=120, container=False, show_label=False)
                    gr.Textbox(value=cfg['api_key'], interactive=False, min_width=120, container=False, show_label=False)
                    
                    status_box = gr.Textbox(
                        value=cfg['status'],
                        interactive=False,
                        min_width=100,
                        container=False,
                        show_label=False
                    )
                    status_textboxes.append(status_box)

                    test_row_btn = gr.Button("🟢 Test", size="sm")
                    delete_row_btn = gr.Button("🗑️ Delete", size="sm")

        # ===== Provider 自动填充 Base URL =====
        def _on_provider_change(selected_provider, current_base_url):
            if selected_provider == "Ollama" and (not current_base_url or current_base_url.strip() == ""):
                return gr.update(value="http://localhost:11434")
            return gr.update()

        provider.change(
            fn=_on_provider_change,
            inputs=[provider, base_url],
            outputs=base_url
        )

        # ===== Submit 事件（占位）=====
        def on_submit(provider_val, model, key, url):
            print(f"[UI] Submit new LLM: {provider_val}/{model}")
            # TODO: 调用真实 handler
            return

        submit_btn.click(
            fn=on_submit,
            inputs=[provider, model_name, api_key, base_url],
            outputs=[]
        )

        # 行按钮事件（占位）
        for i in range(len(mock_configs)):
            test_row_btn.click(
                lambda: print(f"Test clicked"),
                outputs=[]
            )
            delete_row_btn.click(
                lambda: print(f"Delete clicked"),
                outputs=[]
            )

    return llm_ui