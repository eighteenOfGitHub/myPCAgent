# frontend/ui/pages/dashboard_ui.py

import gradio as gr
from pathlib import Path

def render():
    """主页：系统概览与快捷入口"""
    gr.Markdown("""
    # 🏠 PC Agent Dashboard
    
    欢迎使用本地智能体平台！
                
    > [后端api文档](http://127.0.0.1:8000/docs)点这里。注意：若机器无法访问外网或被防火墙拦截，Swagger UI 就是空白
    """)

    # 从根目录下读取README.md并展示
    try:
        project_root = Path(__file__).resolve().parents[3]
        readme_path = project_root / "README.md"
        with readme_path.open("r", encoding="utf-8") as f:
            gr.Markdown(f.read())
    except FileNotFoundError as e:
        gr.Markdown(f"❌ 无法找到 README.md 文件: {e}")