# frontend/ui/pages/dashboard.py

import gradio as gr

def render():
    """主页：系统概览与快捷入口"""
    gr.Markdown("""
    # 🏠 PC Agent Dashboard
    
    欢迎使用本地智能体平台！
                
    > [后端api文档](http://127.0.0.1:8000/docs)点这里
    """)

    # 从根目录下读取README.md并展示
    try:
        with open("../README.md", "r", encoding="utf-8") as f:
            gr.Markdown(f.read())
    except FileNotFoundError:
        pass