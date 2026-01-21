"""
config/env_config.py

共享配置模块。

此模块定义了前后端都需要知道的配置项，并从 config/env_config.yaml 文件加载它们。
"""
import yaml
from pathlib import Path
from typing import List
from pydantic import BaseModel, Field

class EnvConfig(BaseModel):
    """
    共享配置模型。
    """
    APP_VERSION: str = Field(
        default="0.2.x",
        description="应用版本号"
    )
    # 运行环境
    RUN_ENV: str = Field(
        default="development",
        description="运行环境: development, production",
        pattern=r"^(development|production)$" # 使用 pattern 验证字段值
    )
    # --- 服务器配置 (共享) ---
    BACKEND_HOST: str = Field(
        default="127.0.0.1",
        description="后端 FastAPI 服务监听的主机地址"
    )
    BACKEND_PORT: int = Field(
        default=8000,
        description="后端 FastAPI 服务监听的端口"
    )
    FRONTEND_HOST: str = Field(
        default="127.0.0.1",
        description="前端 Gradio 服务监听的主机地址"
    )
    FRONTEND_PORT: int = Field(
        default=7860,
        description="前端 Gradio 服务监听的端口"
    )
        # --- API 相关 ---
    API_BASE_URL: str = Field(
        default=f"http://localhost:{BACKEND_PORT}/api",
        description="后端 API 的基础 URL，前端用于请求后端服务"
    )
    # CORS 源，后端会用这个配置 CORS 中间件，前端也可以用它来校验请求目标
    ALLOWED_API_ORIGINS: List[str] = Field(
        default=[f"http://localhost:{FRONTEND_PORT}", f"http://{FRONTEND_HOST}:{FRONTEND_PORT}"],
        description="允许访问后端 API 的前端源列表"
    )


def load_env_config_from_yaml(yaml_path: Path) -> EnvConfig:
    """
    从 YAML 文件加载共享配置。

    Args:
        yaml_path (Path): YAML 配置文件的路径。

    Returns:
        EnvConfig: 加载并验证后的共享配置实例。
    """
    try:
        with open(yaml_path, 'r', encoding='utf-8') as file:
            config_data = yaml.safe_load(file) or {}
            return EnvConfig(**config_data)
    except FileNotFoundError:
        print(f"警告: 未找到共享配置文件 {yaml_path}，将使用默认值。")
        return EnvConfig()
    except yaml.YAMLError as e:
        print(f"错误: 解析共享配置文件 {yaml_path} 时出错: {e}")
        return EnvConfig()
    except Exception as e:
        print(f"错误: 加载共享配置文件 {yaml_path} 时发生未知错误: {e}")
        return EnvConfig()

# --- 全局共享配置实例 ---
# 从项目根目录下的 config/env_config.yaml 加载
yaml_config_path = Path(__file__).resolve().parent / "env_config.yaml"
env_config = load_env_config_from_yaml(yaml_config_path)

__all__ = ['env_config', 'EnvConfig']