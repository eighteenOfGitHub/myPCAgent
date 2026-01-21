# frontend/ui/pages/llm_setting.py
import gradio as gr
from frontend.handlers import llm_setting # 导入 handlers 模块
from shared.schemas import LLMProvider # 导入枚举，用于类型检查和转换

def create_llm_models_setting_ui(visible=True):
    with gr.Column(visible=visible) as llm_ui:
        gr.Markdown("### 🔧 Manage LLM Models")

        # ui代码代码

        # ===== 添加区域 =====
        with gr.Accordion("➕ Add New LLM", open=False) as add_accordion:
            provider = gr.Dropdown(
                choices=["OpenAI", "Ollama"], # choices 与 LLMProvider 枚举值对应
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
            # 用于显示提交结果的消息
            submit_result = gr.Textbox(label="Result", interactive=False, visible=False)

            # Submit 按钮右下角
            with gr.Row():
                gr.Column(scale=8)
                with gr.Column(scale=2, min_width=120):
                    submit_btn = gr.Button("✅ Submit", variant="primary", size="sm")

        # ===== 管理区域 =====
        gr.Markdown("### 📋 Existing LLM Configurations")

        # 添加刷新按钮
        refresh_btn = gr.Button("🔄 Refresh List", variant="secondary")

        # 替换静态展示为动态 Dataframe
        # 定义列标题，注意可能需要根据后端实际返回字段调整
        llm_config_df = gr.Dataframe(
            label="Current LLM Configurations",
            headers=["ID", "Provider", "Model Name", "Base URL", "Created At", "Updated At"],
            datatype=["number", "str", "str", "str", "str", "str"],
            interactive=False, # 设置为非交互，只用于展示
            elem_id="llm_config_table" # 可选：添加一个 ID 便于 CSS 定制或 JS 操作
        )

        # 控件绑定代码

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

        # ===== Submit 事件关联 =====
        def on_submit(provider_val, model, key, url):
            # 确保 provider_val 是 LLMProvider 枚举中的值
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
                # 提交成功，清空表单并关闭 accordion
                # 返回值为 (provider_update, model_update, api_key_update, base_url_update, result_update)
                return (
                    gr.update(value=None), # 清空 provider
                    gr.update(value=""), # 清空 model_name
                    gr.update(value=""), # 清空 api_key
                    gr.update(value=""), # 清空 base_url
                    gr.update(visible=True, value=f"✅ {message}"), # 显示成功消息
                    gr.update(open=False) # 关闭 accordion
                )
            else:
                # 提交失败，显示错误消息
                return (
                    gr.update(), # 保持 provider 不变
                    gr.update(), # 保持 model_name 不变
                    gr.update(), # 保持 api_key 不变
                    gr.update(), # 保持 base_url 不变
                    gr.update(visible=True, value=f"❌ {message}"), # 显示失败消息
                    gr.update() # 保持 accordion 状态不变
                )

        submit_btn.click(
            fn=on_submit,
            inputs=[provider, model_name, api_key, base_url],
            outputs=[provider, model_name, api_key, base_url, submit_result, add_accordion] # 输出列表
        )

        # ===== Refresh Button Event =====
        def refresh_llm_configs():
            # 调用 handlers 中的函数
            success, data_or_error = llm_setting.get_all_llm_configs()

            if success:
                # 成功获取数据，将其格式化为 Dataframe 需要的格式 (列表的列表)
                if isinstance(data_or_error, list) and len(data_or_error) > 0:
                    # 提取所需字段并组织成行
                    rows = []
                    for config in data_or_error:
                        # 确保字段名与后端返回的 JSON key 匹配
                        row = [
                            config.get('id'),
                            config.get('provider'),
                            config.get('model_name'),
                            config.get('base_url'), # 如果为 None，gradio 会显示为 "(No Value)"
                            config.get('created_at'),
                            config.get('updated_at')
                        ]
                        rows.append(row)
                    # 返回更新 Dataframe 的值
                    return gr.update(value=rows)
                else:
                    # 成功但列表为空
                    return gr.update(value=[])
            else:
                # 获取失败，返回空列表
                # 也可以选择返回错误信息到 dataframe 或其他方式提示
                # 这里选择返回空列表，并可能需要前端其他方式提示错误
                print(f"Warning: Failed to load LLM configs: {data_or_error}") # For debugging, can be removed later
                return gr.update(value=[])

        # 绑定刷新按钮点击事件
        refresh_btn.click(
            fn=refresh_llm_configs,
            inputs=[],
            outputs=[llm_config_df]
        )

    return llm_ui, llm_config_df, refresh_btn 