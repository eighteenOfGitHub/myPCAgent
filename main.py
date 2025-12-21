# main.py（仅删去弹窗线程，其余保持上一版）
from fastapi import FastAPI
from services.api.routers import greetings
from app.web_app import web_app
import uvicorn
from core.config.env_config import EnvConfig
import sys
import logging

def initialize_environment():
    """
    初始化启动环境，特别是配置日志系统。
    - 加载 env_config.yaml 获取运行模式（debug/release）
    - 动态调整单份 logging_config.yaml 的行为，无需多套配置文件
    """
    # --- 第一阶段：加载环境配置 ---
    try:
        env_config = EnvConfig.load()
        is_debug_mode: bool = env_config.debug  # 布尔值，不是字符串
    except (FileNotFoundError, ValueError) as e:
        # 配置文件缺失或格式错误：使用最简日志回退
        logging.basicConfig(
            level=logging.CRITICAL,
            format="%(asctime)s - %(levelname)s - %(message)s",
            force=True,
        )
        logging.critical("❌ 配置加载失败，请检查 config/env_config.yaml 文件。\n错误详情: %s", e)
        sys.exit(1)

    # --- 第二阶段：加载并动态调整日志配置 ---
    try:
        from core.config.logging_config import LoggingConfig

        # 加载基础日志配置（仅一份 YAML）
        base_logging_config: LoggingConfig = LoggingConfig.load()
        config_dict = base_logging_config.model_dump(by_alias=True, exclude_none=True)

        # 根据 debug 模式动态调整
        if is_debug_mode:
            root_level = "DEBUG"
            console_level = "DEBUG"
            enable_console = True
        else:
            root_level = "INFO"
            console_level = "CRITICAL"  # 或直接移除， 最高等级
            enable_console = False

        # 调整 root logger 级别
        config_dict["loggers"][""]["level"] = root_level

        # 调整 console handler 级别（如果存在）
        if "console" in config_dict["handlers"]:
            config_dict["handlers"]["console"]["level"] = console_level

        # 若禁用控制台，从所有 loggers 中移除 console handler
        if not enable_console:
            for logger_conf in config_dict["loggers"].values():
                handlers = logger_conf.get("handlers", [])
                if "console" in handlers:
                    handlers.remove("console")
            config_dict["handlers"].pop("console", None)  # 可选：清理定义

        # 应用最终日志配置
        logging.config.dictConfig(config_dict)

        # 记录启动成功日志
        from core.logger import get_logger
        logger = get_logger(__name__)
        mode_str = "debug" if is_debug_mode else "release"
        logger.info(
            "Started %s v%s in '%s' mode.",
            env_config.name,
            env_config.version,
            mode_str,
        )

    except Exception as e:
        # 日志配置阶段出错：回退到基础日志输出错误
        logging.basicConfig(
            level=logging.CRITICAL,
            format="%(asctime)s - %(levelname)s - %(message)s",
            force=True,
        )
        logging.critical(
            "Failed to initialize logging system from configuration: %s",
            e,
            exc_info=True,
        )
        raise RuntimeError("Critical failure during environment initialization") from e


# app = FastAPI(
#         title="Modular & Integrated PC Agent API",
#         description="一个模块化的 API 示例，集成了 Gradio UI。Greetings API 和 Gradio UI 由同一进程提供服务。",
#         version="1.0.0",
#     )
# # 注册 API 路由
# app.include_router(greetings.router)

# # 把 Gradio 挂到根路径 "/"，FastAPI 的 /docs /redoc 仍可用
# from gradio import mount_gradio_app
# app = mount_gradio_app(app, web_app, path="/")

if __name__ == "__main__":
    initialize_environment()
    # uvicorn.run("main:app", host="localhost", port=8000,
    #             reload=True,          # ← 调试模式 1：文件变动自动重载
    #             reload_dirs=["."],    # 监视当前目录（默认就是当前目录，可省略）
    # )
