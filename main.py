# main.py
from fastapi import FastAPI
from api.routers import greetings
from app.web_app import gradio_app
import uvicorn
from core.config.env_config import EnvConfig
import sys
import logging
import logging.config
from core.config.logging_config import LoggingConfig
from core.logger import get_logger
from core.context import AppContext
import time

def initialize_environment() -> logging.Logger:
    """
    初始化启动环境，特别是配置日志系统。
    
    Returns:
        logging.Logger: 配置好并可用于后续初始化的 Logger 实例。
    """
    # --- 第一阶段：加载环境配置 ---
    try:
        env_config = EnvConfig.load()
        is_debug_mode: bool = env_config.debug  # 布尔值
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
        if "console" in config_dict.get("handlers", {}):
            config_dict["handlers"]["console"]["level"] = console_level

        # 若禁用控制台，从所有 loggers 中移除 console handler
        if not enable_console:
            for logger_conf in config_dict.get("loggers", {}).values():
                handlers = logger_conf.get("handlers", [])
                if "console" in handlers:
                    handlers.remove("console")
            config_dict["handlers"].pop("console", None)  # 可选：清理定义

        # 应用最终日志配置
        logging.config.dictConfig(config_dict)

        # 记录启动成功日志
        # 使用 core.logger 中的 get_logger 获取已配置的 logger
        logger = get_logger(__name__)
        mode_str = "debug" if is_debug_mode else "release"
        logger.info(
            "🚀 Started %s v%s in '%s' mode.",
            env_config.name, env_config.version, mode_str,
        )
        return logger # <-- 返回配置好的 logger

    except Exception as e:
        # 日志配置阶段出错：回退到基础日志输出错误
        logging.basicConfig(
            level=logging.CRITICAL,
            format="%(asctime)s - %(levelname)s - %(message)s",
            force=True,
        )
        logging.critical(
            "💥 Failed to initialize logging system from configuration: %s",
            e,
            exc_info=True,
        )
        raise RuntimeError("Critical failure during environment initialization") from e


def initialize_core_components() -> AppContext:
    """
    完成 core 模块的初始化与准备工作。
    Returns:
        AppContext: 初始化完成的 AppContext 实例。
    """
    logger = get_logger(__name__)
    logger.info("🔧 Starting core components initialization...")
    
    # 1. 获取 AppContext 单例
    app_context = AppContext.get_instance()
    
    # 2. 加载配置文件 (这里假设配置文件都在 config 目录下)
    try:
        env_config = EnvConfig.load()
        logger.debug("✅ Environment config loaded.")
        
        # 注意：日志配置已经在 initialize_environment 中加载和应用了
        # 这里可以加载其他配置，例如 LLM 配置
        from core.config.llm_config import LlmConfig
        llm_config = LlmConfig.load()
        logger.debug("✅ LLM config loaded.")

        # 如果还有其他配置，也在这里加载...
        # from core.config.some_other_config import SomeOtherConfig
        # some_other_config = SomeOtherConfig.load()

    except Exception as e:
        logger.critical("💥 Failed to load core configuration files: %s", e, exc_info=True)
        raise RuntimeError(f"Critical failure loading configurations: {e}") from e

    # 3. 将配置注入 AppContext 并完成核心部件初始化
    try:
        app_context.initialize_components(
            env_config=env_config,
            llm_config=llm_config
            # 如果有其他配置，也需要传入
            # some_other_config=some_other_config
        )
        logger.info("🎉 Core components initialized and injected into AppContext.")
    except Exception as e:
        logger.critical("💥 Failed to initialize core components within AppContext: %s", e, exc_info=True)
        raise RuntimeError(f"Critical failure initializing core components: {e}") from e

    return app_context # <-- 返回初始化完成的 AppContext 实例


def create_app() -> FastAPI:
    # 创建 FastAPI 应用
    app = FastAPI(
            title="Modular & Integrated PC Agent API",
            description="一个模块化的 API 示例，集成了 Gradio UI。Greetings API 和 Gradio UI 由同一进程提供服务。",
            version="0.1.0",
        )
    # 注册 API 路由
    app.include_router(greetings.router)

    # 把 Gradio 挂到根路径 "/"，FastAPI 的 /docs /redoc 仍可用
    from gradio import mount_gradio_app
    app = mount_gradio_app(app, gradio_app, path="/")
    return app

def main():
    # 记录启动时间
    start_time = time.time()
    initialize_environment()
    logger = get_logger(__name__)
    app_context = initialize_core_components()
    end_time = time.time()
    logger.info("🎉 Environment and core components initialized in %.3f seconds.", end_time - start_time)
    logger.info("🚀 Starting Uvicorn server...")
    try:
        uvicorn.run("main:create_app", host="localhost", port=8000, reload=True, factory=True) # <-- 阻塞点
    except KeyboardInterrupt:
        logger.info("🛑 Received interrupt signal (Ctrl+C). Shutting down gracefully...")
    except Exception as e:
        logger.critical(f"💥 Uvicorn server failed to start or crashed: {e}", exc_info=True)
        raise
    finally:
        app_context.close()
        logger.info("🏁 Uvicorn server stopped. Main thread exiting.\n")

if __name__ == "__main__":
    main()