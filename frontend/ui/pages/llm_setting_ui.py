# frontend/ui/pages/llm_setting_ui.py
import gradio as gr
from frontend.handlers.llm_setting_handler import (
    get_all_llm_configs,
    submit_new_llm_config,
    delete_llm_config,
    fetch_default_llm_config_id,
    set_default_llm_config,
    format_ts_to_sec,
    normalize_provider_label,
    build_choices_from_configs,
    build_delete_choices,
    get_selected_default,
    build_rows_from_configs,
    fetch_llm_state,
)
from shared.llm_setting_schemas import LLMProvider

def create_llm_models_setting_ui(visible=True, llm_configs_state=None, default_id_state=None):
    # --- 辅助函数（数据/事件逻辑） ---
    def _build_delete_choices(configs):
        """构建删除下拉框选项"""
        choices = []
        for cfg in configs or []:
            provider_label = normalize_provider_label(cfg.get('provider'))
            label = f"{cfg.get('model_name')} ({provider_label}) [ID: {cfg.get('id')}]"
            choices.append((label, cfg.get('id')))
        return choices

    def _fetch_configs():
        success, data_or_error = get_all_llm_configs()
        return data_or_error if success and isinstance(data_or_error, list) else []

    def _fetch_state():
        return fetch_llm_state()

    def _sync_ui_from_state(configs, default_id):
        choices = build_choices_from_configs(configs, default_id)
        selected = get_selected_default(choices, default_id)
        rows = build_rows_from_configs(configs, default_id)
        delete_choices = build_delete_choices(configs)
        return (
            gr.update(value=rows),
            gr.update(choices=choices, value=selected),
            gr.update(choices=delete_choices, value=None),
        )

    def _on_default_save(default_llm_id, current_configs):
        success, msg, _ = set_default_llm_config(default_llm_id)
        if not success:
            gr.Error(f"❌ {msg}", duration=3)
            return (
                gr.update(),
                gr.update(),
            )
        gr.Info("✅ Saved default model.", duration=3)
        return (
            current_configs,
            default_llm_id,
        )

    def _on_delete_model(selected_id, current_configs, current_default_id):
        """删除模型并刷新状态"""
        if not selected_id:
            gr.Warning("⚠️ 请选择要删除的模型", duration=3)
            return (
                gr.update(),
                gr.update(),
                current_configs,
                current_default_id,
            )
        
        try:
            success = delete_llm_config(selected_id)
            
            if success:
                # 重新获取配置列表
                configs = _fetch_configs()
                # 如果删除的是默认模型，清空默认ID
                new_default_id = None if selected_id == current_default_id else current_default_id
                
                gr.Info("✅ 模型已成功删除", duration=3)
                return (
                    gr.update(choices=_build_delete_choices(configs), value=None),
                    gr.update(open=False),
                    configs,
                    new_default_id,
                )
            else:
                gr.Error("❌ 删除失败，请重试", duration=3)
                return (
                    gr.update(),
                    gr.update(),
                    current_configs,
                    current_default_id,
                )
                
        except Exception as e:
            gr.Error(f"❌ 删除时发生错误: {str(e)}", duration=3)
            return (
                gr.update(),
                gr.update(),
                current_configs,
                current_default_id,
            )

    def _on_provider_change(selected_provider, current_base_url):
        if selected_provider == "Ollama" and (not current_base_url or current_base_url.strip() == ""):
            return gr.update(value="http://localhost:11434")
        return gr.update()

    def _submit_and_refresh_state(provider_val, model, key, url, current_default_id):
        try:
            provider_enum = LLMProvider(provider_val)
        except ValueError:
            gr.Error(f"❌ 无效的 Provider: {provider_val}", duration=3)
            return (
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
            )

        success, message = submit_new_llm_config(
            provider=provider_enum,
            model_name=model,
            api_key=key,
            base_url=url
        )

        if success:
            configs = _fetch_configs()
            gr.Info(f"✅ {message}", duration=3)
            return (
                gr.update(value=None),
                gr.update(value=""),
                gr.update(value=""),
                gr.update(value=""),
                gr.update(open=False),
                configs,
                current_default_id,
            )
        else:
            gr.Error(f"❌ {message}", duration=3)
            return (
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
                gr.update(),
            )

    def _delayed_close_accordion():
        import time
        time.sleep(3)
        return gr.update(open=False)

    # 如果没有传入共享状态，则创建本地状态并初始化
    if llm_configs_state is None or default_id_state is None:
        initial_configs, initial_default_id = fetch_llm_state()
        if llm_configs_state is None:
            llm_configs_state = gr.State(value=initial_configs)
        if default_id_state is None:
            default_id_state = gr.State(value=initial_default_id)
    else:
        # 使用共享状态的当前值作为初始值
        initial_configs = llm_configs_state.value or []
        initial_default_id = default_id_state.value

    initial_choices = build_choices_from_configs(initial_configs, initial_default_id)
    initial_selected = get_selected_default(initial_choices, initial_default_id)
    initial_delete_choices = build_delete_choices(initial_configs)

    # --- UI 布局 ---
    with gr.Column(visible=visible) as llm_ui:

        # ===== 表格区域（最前面） =====
        gr.Markdown("## 📋 LLM Configurations")

        # 使用共享状态（由主布局传入）
        llm_configs_state = llm_configs_state
        default_id_state = default_id_state

        llm_config_df = gr.Dataframe(
            headers=["ID", "Provider", "Model Name", "Default", "Base URL", "Updated At"],
            datatype=["number", "str", "str", "str", "str", "str"],
            interactive=False,
            elem_id="llm_config_table",
            value=build_rows_from_configs(initial_configs, initial_default_id),
            wrap=True,
        )

        # ===== Refresh 按钮（表格右下角） =====
        with gr.Row():
            gr.Column(scale=8)
            with gr.Column(scale=2, min_width=120):
                refresh_btn = gr.Button("🔄 Refresh", variant="secondary", size="sm")

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

        # ===== Delete LLM Model =====
        gr.Markdown("## 🗑️ Delete LLM Model")
        with gr.Accordion("Select model to delete", open=False) as delete_accordion:
            delete_dropdown = gr.Dropdown(
                choices=initial_delete_choices,
                interactive=True,
                allow_custom_value=False,
                show_label=False,
            )
            with gr.Row():
                gr.Column(scale=8)
                with gr.Column(scale=2, min_width=120):
                    delete_model_btn = gr.Button("🗑️ Delete", variant="stop", size="sm")

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
            outputs=[llm_config_df, default_llm_dropdown, delete_dropdown],
        )

        add_model_submit_btn.click(
            fn=_submit_and_refresh_state,
            inputs=[provider, model_name, api_key, base_url, default_id_state],
            outputs=[provider, model_name, api_key, base_url, add_accordion, llm_configs_state, default_id_state]
        ).then(
            fn=_sync_ui_from_state,
            inputs=[llm_configs_state, default_id_state],
            outputs=[llm_config_df, default_llm_dropdown, delete_dropdown],
        ).then(
            fn=_delayed_close_accordion,
            inputs=[],
            outputs=[add_accordion],
            show_progress="hidden"
        )

        default_submit_btn.click(
            fn=_on_default_save,
            inputs=[default_llm_dropdown, llm_configs_state],
            outputs=[llm_configs_state, default_id_state],
        ).then(
            fn=_sync_ui_from_state,
            inputs=[llm_configs_state, default_id_state],
            outputs=[llm_config_df, default_llm_dropdown, delete_dropdown],
        )

        delete_model_btn.click(
            fn=_on_delete_model,
            inputs=[delete_dropdown, llm_configs_state, default_id_state],
            outputs=[delete_dropdown, delete_accordion, llm_configs_state, default_id_state],
        ).then(
            fn=_sync_ui_from_state,
            inputs=[llm_configs_state, default_id_state],
            outputs=[llm_config_df, default_llm_dropdown, delete_dropdown],
        ).then(
            fn=_delayed_close_accordion,
            inputs=[],
            outputs=[delete_accordion],
            show_progress="hidden"
        )

    # 返回状态引用，供主布局监听
    return llm_ui, llm_config_df, llm_configs_state, default_id_state