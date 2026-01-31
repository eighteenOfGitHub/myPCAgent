# frontend/ui/pages/llm_setting_ui.py
import gradio as gr
from frontend.handlers.llm_setting_handler import get_all_llm_configs, submit_new_llm_config
from frontend.handlers.preference_setting_handler import (
    fetch_default_llm_config_id,
    set_default_llm_config,
)
from shared.llm_setting_schemas import LLMProvider

def create_llm_models_setting_ui(visible=True):
    # --- 辅助函数（数据/事件逻辑） ---
    def _format_ts_to_sec(value):
        if not value:
            return value
        if isinstance(value, str):
            return value[:19].replace("T", " ")
        try:
            return value.strftime("%Y-%m-%d %H:%M:%S")
        except Exception:
            return value

    def _is_default(row_id, default_id):
        if default_id is None or row_id is None:
            return ""
        return "√" if str(row_id) == str(default_id) else ""

    def _mark_default_choice(choices, default_id):
        if not default_id:
            return choices
        marked = []
        for label, value in choices:
            if value == default_id:
                label = f"{label}(default model)"
            marked.append((label, value))
        return marked

    def _normalize_provider_label(provider):
        if hasattr(provider, "value"):
            return provider.value
        if isinstance(provider, str) and provider.startswith("LLMProvider."):
            return provider.split(".", 1)[1].title()
        return str(provider) if provider is not None else ""

    def _build_choices_from_configs(configs, default_id):
        choices = []
        for cfg in configs or []:
            provider_label = _normalize_provider_label(cfg.get('provider'))
            label = f"{provider_label} / {cfg.get('model_name')}"
            choices.append((label, cfg.get("id")))
        return _mark_default_choice(choices, default_id)

    def _get_selected_default(choices, default_id):
        if choices and any(c[1] == default_id for c in choices):
            return default_id
        return choices[0][1] if choices else None

    def _build_rows_from_configs(configs, default_id):
        rows = []
        for config in configs or []:
            row_id = config.get('id')
            rows.append([
                row_id,
                config.get('provider'),
                config.get('model_name'),
                _is_default(row_id, default_id),
                config.get('base_url'),
                _format_ts_to_sec(config.get('updated_at'))
            ])
        return rows

    def _fetch_configs():
        success, data_or_error = get_all_llm_configs()
        return data_or_error if success and isinstance(data_or_error, list) else []

    def _fetch_state():
        configs = _fetch_configs()
        default_id = fetch_default_llm_config_id()
        return configs, default_id

    def _sync_ui_from_state(configs, default_id):
        choices = _build_choices_from_configs(configs, default_id)
        selected = _get_selected_default(choices, default_id)
        rows = _build_rows_from_configs(configs, default_id)
        return (
            gr.update(value=rows),
            gr.update(choices=choices, value=selected),
        )

    def _on_default_save(default_llm_id, current_configs):
        success, msg, _ = set_default_llm_config(default_llm_id)
        if not success:
            return (
                gr.update(),
                gr.update(),
                gr.update(value=f"❌ {msg}", visible=True),
                gr.update(active=True),
            )
        return (
            current_configs,
            default_llm_id,
            gr.update(value="✅ Saved default model.", visible=True),
            gr.update(active=True),
        )

    def _on_provider_change(selected_provider, current_base_url):
        if selected_provider == "Ollama" and (not current_base_url or current_base_url.strip() == ""):
            return gr.update(value="http://localhost:11434")
        return gr.update()

    def _submit_and_refresh_state(provider_val, model, key, url, current_default_id):
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
                gr.update(),
                gr.update(),
                gr.update(active=True),
            )

        success, message = submit_new_llm_config(
            provider=provider_enum,
            model_name=model,
            api_key=key,
            base_url=url
        )

        if success:
            configs = _fetch_configs()
            return (
                gr.update(value=None),
                gr.update(value=""),
                gr.update(value=""),
                gr.update(value=""),
                gr.update(visible=True, value=f"✅ {message}"),
                gr.update(open=False),
                configs,
                current_default_id,
                gr.update(active=True),
            )
        else:
            return (
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(visible=True, value=f"❌ {message}"),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(active=True),
            )

    def _delayed_close_accordion():
        # 重要过程：延迟 3 秒后关闭 Accordion
        import time
        time.sleep(3)
        return gr.update(open=False)

    def _hide_default_status():
        return (
            gr.update(value="", visible=False),
            gr.update(active=False),
        )

    initial_configs, initial_default_id = _fetch_state()
    initial_choices = _build_choices_from_configs(initial_configs, initial_default_id)
    initial_selected = _get_selected_default(initial_choices, initial_default_id)

    # --- UI 布局 ---
    with gr.Column(visible=visible) as llm_ui:

        # ===== 表格区域（最前面） =====
        gr.Markdown("## 📋 LLM Configurations")

        llm_configs_state = gr.State(value=initial_configs)
        default_id_state = gr.State(value=initial_default_id)

        llm_config_df = gr.Dataframe(
            headers=["ID", "Provider", "Model Name", "Default", "Base URL", "Updated At"],
            datatype=["number", "str", "str", "str", "str", "str"],
            interactive=False,
            elem_id="llm_config_table",
            value=_build_rows_from_configs(initial_configs, initial_default_id),
            wrap=True,
        )

        # ===== Refresh 按钮（表格右下角） =====
        with gr.Row():
            gr.Column(scale=8)
            with gr.Column(scale=2, min_width=120):
                refresh_btn = gr.Button("🔄 Refresh", variant="refresh", size="sm")

        # ===== Default LLM Model =====
        gr.Markdown("## 🧠 Set Default LLM Model")

        with gr.Accordion("Fill out the form", open=False) as default_accordion:
            default_llm_dropdown = gr.Dropdown(
                choices=initial_choices,
                value=initial_selected,
                interactive=True,
                allow_custom_value=False,
                show_label=False,
            )
            with gr.Row():
                gr.Column(scale=8)
                with gr.Column(scale=2, min_width=120):
                    default_submit_btn = gr.Button("✅ Submit", variant="primary", size="sm")

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

            with gr.Row():
                gr.Column(scale=8)
                with gr.Column(scale=2, min_width=120):
                    add_model_submit_btn = gr.Button("✅ Submit", variant="primary", size="sm")

        shared_status_text = gr.Textbox(value="", show_label=False, interactive=False, visible=False)
        shared_status_timer = gr.Timer(3.0, active=False)

        # --- 控件绑定（集中注册） ---
        provider.change(
            fn=_on_provider_change,
            inputs=[provider, base_url],
            outputs=base_url
        )

        refresh_btn.click(
            fn=_fetch_state,
            inputs=[],
            outputs=[llm_configs_state, default_id_state],
        ).then(
            fn=_sync_ui_from_state,
            inputs=[llm_configs_state, default_id_state],
            outputs=[llm_config_df, default_llm_dropdown],
        )

        add_model_submit_btn.click(
            fn=_submit_and_refresh_state,
            inputs=[provider, model_name, api_key, base_url, default_id_state],
            outputs=[provider, model_name, api_key, base_url, shared_status_text, add_accordion, llm_configs_state, default_id_state, shared_status_timer]
        ).then(
            fn=_sync_ui_from_state,
            inputs=[llm_configs_state, default_id_state],
            outputs=[llm_config_df, default_llm_dropdown],
        ).then(
            fn=_delayed_close_accordion,
            inputs=[],
            outputs=[add_accordion],
            show_progress="hidden"
        )

        default_submit_btn.click(
            fn=_on_default_save,
            inputs=[default_llm_dropdown, llm_configs_state],
            outputs=[llm_configs_state, default_id_state, shared_status_text, shared_status_timer],
        ).then(
            fn=_sync_ui_from_state,
            inputs=[llm_configs_state, default_id_state],
            outputs=[llm_config_df, default_llm_dropdown],
        )

        shared_status_timer.tick(
            fn=_hide_default_status,
            inputs=[],
            outputs=[shared_status_text, shared_status_timer],
        )

    return llm_ui, llm_config_df