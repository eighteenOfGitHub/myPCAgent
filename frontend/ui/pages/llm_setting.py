# frontend/ui/pages/llm_setting.py
import gradio as gr
from frontend.handlers import llm_setting
from shared.llm_setting import LLMProvider

def create_llm_models_setting_ui(visible=True):
    # === 辅助函数（数据与事件逻辑） ==========================================
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

    def _on_provider_change(selected_provider, current_base_url):
        if selected_provider == "Ollama" and (not current_base_url or current_base_url.strip() == ""):
            return gr.update(value="http://localhost:11434")
        return gr.update()

    def on_submit(provider_val, model, key, url):
        try:
            provider_enum = LLMProvider(provider_val)
        except ValueError:
            return gr.update(visible=True, value=f"❌ 无效的 Provider: {provider_val}")

        success, message = llm_setting.submit_new_llm_config(
            provider=provider_enum,
            model_name=model,
            api_key=key,
            base_url=url
        )

        if success:
            return (
                gr.update(value=None),
                gr.update(value=""),
                gr.update(value=""),
                gr.update(value=""),
                gr.update(visible=True, value=f"✅ {message}"),
                gr.update(open=False)
            )
        else:
            return (
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(visible=True, value=f"❌ {message}"),
                gr.update()
            )

    def refresh_llm_configs():
        success, data_or_error = llm_setting.get_all_llm_configs()
        if success:
            if isinstance(data_or_error, list) and len(data_or_error) > 0:
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
                return gr.update(value=rows)
            else:
                return gr.update(value=[])
        else:
            print(f"Warning: Failed to load LLM configs: {data_or_error}")
            return gr.update(value=[])

    # === UI 布局（仅 UI 组件） ===============================================
    with gr.Column(visible=visible) as llm_ui:
        gr.Markdown("### 🔧 Manage LLM Models")

        # -- 添加模型区域 ------------------------------------------------------
        with gr.Accordion("➕ Add New LLM", open=False) as add_accordion:
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

        # -- 管理区域（标题与刷新同一行：左文右钮） -----------------------------
        with gr.Row():
            with gr.Column(scale=8):
                gr.Markdown("### 📋 Existing LLM Configurations")
            with gr.Column(scale=2, min_width=120):
                refresh_btn = gr.Button("🔄 Refresh List", variant="secondary")

        # -- 配置表格（只读、可换行、可选择复制） -------------------------------
        llm_config_df = gr.Dataframe(
            label="Current LLM Configurations",
            headers=["ID", "Provider", "Model Name", "Base URL", "Created At", "Updated At"],
            datatype=["number", "str", "str", "str", "str", "str"],
            interactive=False,
            wrap=True,
            elem_id="llm_config_table",
            value=_initial_rows(),
            type="array",  # 明确输出为数组，便于 refresh 回写
        )
        gr.HTML("""
            <style>
            #llm_config_table table, #llm_config_table table * {
                user-select: text !important;
                -webkit-user-select: text !important;
                cursor: text;
            }
            </style>
        """)

    # === 控件绑定（事件注册，仅绑定不改 UI） ==================================
    provider.change(
        fn=_on_provider_change,
        inputs=[provider, base_url],
        outputs=base_url
    )

    submit_btn.click(
        fn=on_submit,
        inputs=[provider, model_name, api_key, base_url],
        outputs=[provider, model_name, api_key, base_url, submit_result, add_accordion]
    )

    refresh_btn.click(
        fn=refresh_llm_configs,
        inputs=[],
        outputs=[llm_config_df]
    )

    return llm_ui, llm_config_df, refresh_btn