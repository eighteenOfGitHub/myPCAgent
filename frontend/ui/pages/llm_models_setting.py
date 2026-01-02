# frontend/ui/pages/llm_models_setting.py
import gradio as gr
from frontend.handlers import llm_models_setting  # 导入 handlers 模块
from shared.schemas import LLMProvider  # 导入枚举，用于类型检查和转换


def create_llm_models_setting_ui(visible=True):
    with gr.Column(visible=visible) as llm_ui:
        gr.Markdown("### 🔧 Manage LLM Models")

        # ===== 添加区域 =====
        with gr.Accordion("➕ Add New LLM", open=False) as add_accordion:
            provider = gr.Dropdown(
                choices=["OpenAI", "Ollama"],  # choices 与 LLMProvider 枚举值对应
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

        # 注意：这里使用真实的后端 API 获取列表，而不是 mock
        # mock_configs = [
        #     {"id": 1, "provider": "OpenAI", "model": "gpt-4o", "api_key": "sk-****1234", "status": "✅ Ready"},
        #     {"id": 2, "provider": "Ollama", "model": "llama3", "api_key": "N/A", "status": "⚠️ Not tested"}
        # ]

        # 为了简化，这里仍使用静态展示，但按钮事件已关联
        # 真实项目中，这里应通过 gr.update 动态刷新
        with gr.Column(variant="panel"):
            # 使用 Gradio 的 update 机制会更复杂，这里简化为静态展示
            # 实际上，你需要一个刷新函数来更新这个列表
            gr.Markdown("*(列表需要从后端动态加载，此处为示例)*")
            with gr.Row():
                gr.Textbox(value="Provider", interactive=False, min_width=80, container=False, show_label=False)
                gr.Textbox(value="Model", interactive=False, min_width=120, container=False, show_label=False)
                gr.Textbox(value="API Key (Masked)", interactive=False, min_width=120, container=False, show_label=False)
                gr.Textbox(value="Status", interactive=False, min_width=100, container=False, show_label=False)
                gr.Button("🟢 Test", size="sm", interactive=False) # 占位
                gr.Button("🗑️ Delete", size="sm", interactive=False) # 占位

            # 示例行
            with gr.Row():
                gr.Textbox(value="OpenAI", interactive=False, min_width=80, container=False, show_label=False)
                gr.Textbox(value="gpt-4o", interactive=False, min_width=120, container=False, show_label=False)
                gr.Textbox(value="sk-****1234", interactive=False, min_width=120, container=False, show_label=False)
                status_box_example = gr.Textbox(value="❓ Pending", interactive=False, min_width=100, container=False, show_label=False)
                test_btn_example = gr.Button("🟢 Test", size="sm")
                delete_btn_example = gr.Button("🗑️ Delete", size="sm")

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

            success, message = llm_models_setting.submit_new_llm_config(
                provider=provider_enum,
                model_name=model,
                api_key=key,
                base_url=url
            )
            if success:
                # 提交成功，清空表单并关闭 accordion
                # 返回值为 (provider_update, model_update, api_key_update, base_url_update, result_update)
                return (
                    gr.update(value=None),  # 清空 provider
                    gr.update(value=""),   # 清空 model_name
                    gr.update(value=""),   # 清空 api_key
                    gr.update(value=""),   # 清空 base_url
                    gr.update(visible=True, value=f"✅ {message}"), # 显示成功消息
                    gr.update(open=False)  # 关闭 accordion
                )
            else:
                # 提交失败，显示错误消息
                return (
                    gr.update(),  # 保持 provider 不变
                    gr.update(),  # 保持 model_name 不变
                    gr.update(),  # 保持 api_key 不变
                    gr.update(),  # 保持 base_url 不变
                    gr.update(visible=True, value=f"❌ {message}"), # 显示失败消息
                    gr.update()   # 保持 accordion 状态不变
                )

        submit_btn.click(
            fn=on_submit,
            inputs=[provider, model_name, api_key, base_url],
            outputs=[provider, model_name, api_key, base_url, submit_result, add_accordion] # 输出列表
        )

        # ===== 行按钮事件关联 (示例) =====
        # 注意：对于动态列表，需要更复杂的机制来处理每个按钮的事件
        # 这里仅为示例行的按钮做演示
        def on_test_click():
            # 示例：测试 ID 为 1 的配置
            message = llm_models_setting.test_existing_llm_config(config_id=1)
            # 在实际应用中，你需要知道点击的是哪一行，可以通过一个隐藏的 ID 输入组件传递
            # 或者，点击后刷新整个列表
            return message

        def on_delete_click():
            # 示例：删除 ID 为 1 的配置
            success = llm_models_setting.delete_llm_config(config_id=1)
            # 在实际应用中，你需要知道点击的是哪一行
            # 点击后通常需要刷新列表
            return "✅ 删除成功" if success else "❌ 删除失败"

        # 这里只是将示例按钮关联到 handlers
        test_btn_example.click(
            fn=on_test_click,
            inputs=[],
            outputs=[status_box_example] # 假设将结果显示在 status_box 上
        )
        delete_btn_example.click(
            fn=on_delete_click,
            inputs=[],
            outputs=[] # 可能需要刷新整个列表组件
        )

    return llm_ui