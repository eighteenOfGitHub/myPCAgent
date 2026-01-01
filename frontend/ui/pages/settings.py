# frontend/ui/pages/settings.py

import gradio as gr

def render():
    """设置页面：LLM 配置管理"""
    gr.Markdown("""
    # ⚙️ 系统设置
    
    ## 模型配置
    - 管理 OpenAI / Ollama 等模型接入
    - 设置默认会话参数
    
    ## API 密钥
    - 安全存储密钥（仅内存，不落盘）
    
    > 功能开发中...
    """)