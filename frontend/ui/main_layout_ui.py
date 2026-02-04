# frontend/ui/main_layout_ui.py
import gradio as gr
from frontend.ui.pages import dashboard, chat, agent, settings
from frontend.handlers.chat_handler import load_session_list
from frontend.handlers.llm_setting_handler import fetch_llm_state, build_choices_from_configs

def create_gradio_interface():
    """
    创建主 Gradio 界面，使用 Tabs 组织多页面
    """
    
    # --- 辅助函数（数据/事件逻辑） ---
    def _init_llm_state():
        """初始化 LLM 配置状态（跨页面共享）"""
        configs, default_id = fetch_llm_state()
        return configs, default_id
    
    def _init_sessions():
        """初始化会话列表"""
        return load_session_list()
    
    def _sync_chat_dropdown(configs, default_id):
        """监听状态变化，更新 Chat 页面下拉框"""
        choices = build_choices_from_configs(configs, default_id)
        return gr.update(choices=choices, value=default_id)
    
    # --- UI 布局 ---
    with gr.Blocks(title="PC Agent") as demo:
        # 创建共享状态（初始为空，由 .load() 填充）
        llm_configs_state = gr.State(value=[])
        default_id_state = gr.State(value=None)
        
        with gr.Tabs():
            with gr.Tab("🏠 Dashboard"):
                dashboard()
            
            with gr.Tab("💬 Chat"):
                session_dropdown, chat_model_dropdown = chat(
                    llm_configs_state=llm_configs_state, 
                    default_id_state=default_id_state
                )
            
            with gr.Tab("🤖 Agent"):
                agent()
            
            with gr.Tab("⚙️ Settings"):
                settings_result = settings(
                    llm_configs_state=llm_configs_state, 
                    default_id_state=default_id_state
                )

        # --- 控件绑定（集中注册） ---
        
        # 1️⃣ 页面加载时初始化 LLM 配置（跨页面共享）
        demo.load(
            fn=_init_llm_state,
            inputs=[],
            outputs=[llm_configs_state, default_id_state],
            show_progress="hidden"
        )
        
        # 2️⃣ 页面加载时初始化会话列表（Chat 页面专用）
        demo.load(
            fn=_init_sessions,
            inputs=[],
            outputs=[session_dropdown],
            show_progress="hidden"
        )
        
        # 3️⃣ Settings 修改时同步到 Chat（状态变化触发）
        llm_configs_state.change(
            fn=_sync_chat_dropdown,
            inputs=[llm_configs_state, default_id_state],
            outputs=[chat_model_dropdown],
        )
        
        default_id_state.change(
            fn=_sync_chat_dropdown,
            inputs=[llm_configs_state, default_id_state],
            outputs=[chat_model_dropdown],
        )
    
    return demo