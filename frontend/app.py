# frontend/app.py
import sys
from pathlib import Path

# 添加项目根目录到 sys.path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from frontend.ui.main_layout_ui import create_gradio_interface
from config.env_config import env_config

# 创建界面并启用队列
demo = create_gradio_interface().queue(
    max_size=20,
    default_concurrency_limit=5
)

if __name__ == "__main__":
    print(f"正在启动前端服务，地址: http://{env_config.FRONTEND_HOST}:{env_config.FRONTEND_PORT}")
    demo.launch(
        server_name=env_config.FRONTEND_HOST,
        server_port=env_config.FRONTEND_PORT,
        show_error=True
    )