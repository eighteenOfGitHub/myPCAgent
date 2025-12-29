"""
backend/config/back_config.py

应用配置管理模块。
"""
import yaml
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field

from config.env_config import env_config



# --- 配置模型 ---
class BackConfig(BaseModel):
    """
    应用配置模型，定义了所有可配置的参数。
    """
    # --- 后端服务器配置 ---
    API_VERSION: str = Field(default="v1", description="API 版本号")
    BACKEND_HOST: str = Field(default="127.0.0.1", description="后端 FastAPI 服务监听的主机地址")
    BACKEND_PORT: int = Field(default=8000, description="后端 FastAPI 服务监听的端口")
    BACKEND_RELOAD: bool = Field(default=True, description="是否开启代码热重载 (开发模式)")
    FRONTEND_HOST: str = Field(default="127.0.0.1", description="前端 Gradio 服务监听的主机地址")
    FRONTEND_PORT: int = Field(default=7860, description="前端 Gradio 服务监听的端口")

    # --- CORS 配置 ---
    ALLOWED_ORIGINS: List[str] = Field(
        default=[f"http://{env_config.FRONTEND_HOST}:{env_config.FRONTEND_PORT}", f"http://localhost:{env_config.FRONTEND_PORT}"], # 默认允许前端访问
        description="允许跨域请求的源列表"
    )

    def __init__(self):
        super().__init__()

        self.BACKEND_HOST = env_config.BACKEND_HOST
        self.BACKEND_PORT = env_config.BACKEND_PORT
        self.BACKEND_RELOAD = True if env_config.RUN_ENV == 'development' else False
        self.ALLOWED_ORIGINS = env_config.ALLOWED_API_ORIGINS




def load_yaml_config(yaml_path: Path) -> dict:
    """
    从 YAML 文件加载配置。

    Args:
        yaml_path (Path): YAML 配置文件的路径。

    Returns:
        dict: 从 YAML 文件解析出的配置字典。
    """
    try:
        with open(yaml_path, 'r', encoding='utf-8') as file:
            config_data = yaml.safe_load(file)
            if config_data is None:
                print(f"警告: {yaml_path} 文件为空或无效，将使用默认配置。")
                return {}
            return config_data
    except FileNotFoundError:
        print(f"警告: 未找到配置文件 {yaml_path}，将使用默认配置。")
        return {}
    except yaml.YAMLError as e:
        print(f"错误: 解析 YAML 配置文件 {yaml_path} 时出错: {e}")
        return {}
    except Exception as e:
        print(f"错误: 加载配置文件 {yaml_path} 时发生未知错误: {e}")
        return {}

back_config = BackConfig()

# --- 导出配置实例 ---
# 在模块级别导出，供其他模块导入使用
__all__ = ['back_config']

# --- 示例用法 ---
if __name__ == "__main__":
    # 打印当前加载的配置
    print("当前配置:")
    print(f"  - 后端地址: {back_config.BACKEND_HOST}:{back_config.BACKEND_PORT}")
    print(f"  - 前端地址: {back_config.FRONTEND_HOST}:{back_config.FRONTEND_PORT}")
    print(f"  - 允许的源: {back_config.ALLOWED_ORIGINS}")
