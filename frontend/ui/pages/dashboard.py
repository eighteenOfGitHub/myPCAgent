# frontend/ui/pages/dashboard.py

import gradio as gr

def render():
    """主页：系统概览与快捷入口"""
    gr.Markdown("""
    # 🏠 PC Agent Dashboard
    
    欢迎使用本地智能体平台！
    
    ## 快捷操作
    - 点击 **💬 Chat** 开始对话
    - 在 **⚙️ Settings** 中配置模型
    - **🤖 Agent** 页面即将支持自定义工作流
    
    > 当前版本：v0.1.1 | 后端状态：✅ 正常
    """)