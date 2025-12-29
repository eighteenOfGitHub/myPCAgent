"""
frontend/app.py

Gradio 前端应用的启动入口点。

此模块负责加载 UI 并启动 Gradio 服务。
"""
from frontend.ui.dashboard import create_gradio_interface
from config.env_config import env_config

def run_gradio_app():
    """
    启动 Gradio 应用。
    """
    demo = create_gradio_interface()
    demo.launch(
        server_name=env_config.FRONTEND_HOST,
        server_port=env_config.FRONTEND_PORT,
        share=False, # 默认不创建公共链接
        show_error=True,
        debug=True if env_config.RUN_ENV == 'development' else False, # 开发时启用调试模式
    )

if __name__ == "__main__":
    print(f"正在启动前端服务，地址: {env_config.FRONTEND_HOST}:{env_config.FRONTEND_PORT}")
    run_gradio_app()