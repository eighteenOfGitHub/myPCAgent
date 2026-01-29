# frontend/ui/pages/llm_setting.py
import gradio as gr
from frontend.handlers import llm_setting
from shared.llm_setting import LLMProvider

def create_llm_models_setting_ui(visible=True):
    with gr.Column(visible=visible) as llm_ui:

        # ===== 表格区域（最前面） =====
        gr.Markdown("## 📋 LLM Configurations")

        def _initial_rows():
            success, data_or_error = llm_setting.get_all_llm_configs()
            if success and isinstance(data_or_error, list):
                rows = []
                for config in data_or_error:
                    rows.append([
                        config.get('id'),
                        config.get('provider'),
                        config.get('model_name'),
                        config.get('base_url'),
                        config.get('created_at'),
                        config.get('updated_at')
                    ])
                return rows
            return []

        llm_config_df = gr.Dataframe(
            headers=["ID", "Provider", "Model Name", "Base URL", "Created At", "Updated At"],
            datatype=["number", "str", "str", "str", "str", "str"],
            interactive=False,
            elem_id="llm_config_table",
            value=_initial_rows(),
            wrap=True,
        )

        # ===== 刷新按钮（右侧） =====
        with gr.Row():
            gr.Column(scale=4)  # 左侧空白
            with gr.Column(scale=1, min_width=100):
                refresh_btn = gr.Button("🔄 Refresh", variant="secondary")

        # ===== 添加区域（下一行，占满宽度） =====
        gr.Markdown("## ➕ Add New LLM Configuration")
        with gr.Accordion("Fill out the form", open=False) as add_accordion:
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
            submit_result = gr.Textbox(label="Result", interactive=False, visible=False)

            with gr.Row():
                gr.Column(scale=8)
                with gr.Column(scale=2, min_width=120):
                    submit_btn = gr.Button("✅ Submit", variant="primary", size="sm")

        # ===== 控件绑定代码 =====
        def _on_provider_change(selected_provider, current_base_url):
            if selected_provider == "Ollama" and (not current_base_url or current_base_url.strip() == ""):
                return gr.update(value="http://localhost:11434")
            return gr.update()

        provider.change(
            fn=_on_provider_change,
            inputs=[provider, base_url],
            outputs=base_url
        )

        def _refresh_llm_configs():
            # 重要过程：刷新表格数据，返回 Dataframe 的更新值
            success, data_or_error = llm_setting.get_all_llm_configs()
            if success and isinstance(data_or_error, list) and len(data_or_error) > 0:
                rows = []
                for config in data_or_error:
                    row = [
                        config.get('id'),
                        config.get('provider'),
                        config.get('model_name'),
                        config.get('base_url'),
                        config.get('created_at'),
                        config.get('updated_at')
                    ]
                    rows.append(row)
                return gr.update(value=rows)
            else:
                return gr.update(value=[])

        def on_submit(provider_val, model, key, url):
            # 重要过程：提交表单并获得结果
            try:
                provider_enum = LLMProvider(provider_val)
            except ValueError:
                return (
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(visible=True, value=f"❌ 无效的 Provider: {provider_val}"),
                    gr.update(),
                    gr.update()
                )

            success, message = llm_setting.submit_new_llm_config(
                provider=provider_enum,
                model_name=model,
                api_key=key,
                base_url=url
            )

            if success:
                updated_df = _refresh_llm_configs()
                return (
                    gr.update(value=None),
                    gr.update(value=""),
                    gr.update(value=""),
                    gr.update(value=""),
                    gr.update(visible=True, value=f"✅ {message}"),
                    gr.update(open=False),
                    updated_df
                )
            else:
                return (
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(),
                    gr.update(visible=True, value=f"❌ {message}"),
                    gr.update(),
                    gr.update()
                )

        def _delayed_close_accordion():
            # 重要过程：延迟 3 秒后关闭 Accordion
            import time
            time.sleep(3)
            return gr.update(open=False)

        submit_btn.click(
            fn=on_submit,
            inputs=[provider, model_name, api_key, base_url],
            outputs=[provider, model_name, api_key, base_url, submit_result, add_accordion, llm_config_df]
        ).then(
            fn=_delayed_close_accordion,
            inputs=[],
            outputs=[add_accordion],
            show_progress="hidden"
        )

        # ===== 刷新按钮事件 =====
        refresh_btn.click(
            fn=_refresh_llm_configs,
            inputs=[],
            outputs=[llm_config_df]
        )

    return llm_ui, llm_config_df, refresh_btn