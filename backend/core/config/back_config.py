"""backend/config/back_config.py 应用配置管理模块。"""
import yaml
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel, Field
from config.env_config import env_config



# --- 数据库配置子模型 ---
class DatabaseConfig(BaseModel):
    data_dir: str = Field(default="backend/data", description="数据库文件存储目录（相对于项目根目录）")
    db_filename: str = Field(default="pcagent.db", description="数据库文件名")

# --- 主配置模型 ---
class BackConfig(BaseModel):
    # --- 后端服务器配置 ---
    BACKEND_HOST: str = Field(default="127.0.0.1", description="后端 FastAPI 服务监听的主机地址")
    BACKEND_PORT: int = Field(default=8000, description="后端 FastAPI 服务监听的端口")
    BACKEND_RELOAD: bool = Field(default=True, description="是否开启代码热重载 (开发模式)")
    FRONTEND_HOST: str = Field(default="127.0.0.1", description="前端 Gradio 服务监听的主机地址")
    FRONTEND_PORT: int = Field(default=7860, description="前端 Gradio 服务监听的端口")

    # --- CORS 配置 ---
    ALLOWED_ORIGINS: List[str] = Field(
        default=[f"http://{env_config.FRONTEND_HOST}:{env_config.FRONTEND_PORT}", f"http://localhost:{env_config.FRONTEND_PORT}"],
        description="允许跨域请求的源列表"
    )

    # --- 数据库配置 ---
    DATABASE: DatabaseConfig = Field(default_factory=DatabaseConfig)

    def __init__(self):
        # 调用父类初始化（Pydantic 兼容）
        super().__init__()

        # 从环境变量覆盖（保留你原有逻辑）
        self.BACKEND_HOST = env_config.BACKEND_HOST
        self.BACKEND_PORT = env_config.BACKEND_PORT
        self.BACKEND_RELOAD = True if env_config.RUN_ENV == 'development' else False
        self.ALLOWED_ORIGINS = env_config.ALLOWED_API_ORIGINS

        # 从 YAML 文件加载配置（优先级高于默认值，但低于环境变量）
        yaml_path = Path(__file__).parent / "back_config.yaml"
        yaml_data = self._load_yaml_config(yaml_path)

        if yaml_data and "database" in yaml_data:
            db_dict = yaml_data["database"]
            # 只覆盖 YAML 中明确指定的字段
            updated_db = {
                "data_dir": db_dict.get("data_dir", self.DATABASE.data_dir),
                "db_filename": db_dict.get("db_filename", self.DATABASE.db_filename)
            }
            self.DATABASE = DatabaseConfig(**updated_db)

    @staticmethod
    def _load_yaml_config(yaml_path: Path) -> dict:
        """从 YAML 文件安全加载配置。"""
        try:
            with open(yaml_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file) or {}
        except FileNotFoundError:
            print(f"警告: 未找到配置文件 {yaml_path}，使用默认配置。")
            return {}
        except yaml.YAMLError as e:
            print(f"错误: 解析 YAML 文件 {yaml_path} 失败: {e}")
            return {}
        except Exception as e:
            print(f"错误: 加载配置文件 {yaml_path} 时发生未知错误: {e}")
            return {}

# 创建全局配置实例
back_config = BackConfig()

__all__ = ['back_config']