# frontend/ui/pages/agent.py

import gradio as gr

def render():
    """智能体页面：未来支持自定义 Agent 工作流"""
    gr.Markdown("""
    # 🤖 Agent 管理（开发中）
    
    此页面将支持：
    - 创建自定义智能体
    - 配置工具（搜索、计算、文件等）
    - 调试执行流程
    
    > 敬请期待...
    """)