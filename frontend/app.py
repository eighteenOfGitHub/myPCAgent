# frontend/app.py
from frontend.ui.main_layout import create_gradio_interface  # 注意：稍后会创建 main_layout.py
from config.env_config import env_config

# 创建界面并启用队列
demo = create_gradio_interface().queue(
    max_size=20,          # 最大排队请求数（防爆）
    default_concurrency_limit=5  # 默认并发数（可选）
)

if __name__ == "__main__":
    print(f"正在启动前端服务，地址: http://{env_config.FRONTEND_HOST}:{env_config.FRONTEND_PORT}")
    demo.launch(
        server_name=env_config.FRONTEND_HOST,
        server_port=env_config.FRONTEND_PORT,
        share=False,
        show_error=True,
        debug=(env_config.RUN_ENV == 'development')
    )