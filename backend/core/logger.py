# backend/core/logger.py

import logging
import logging.config
import yaml
from pythonjsonlogger import jsonlogger
from pathlib import Path
import time
from config.env_config import env_config

# 定义日志配置文件路径
LOG_CONFIG_PATH = Path(__file__).parent.parent / "core" / "config" / "log_config.yaml"

class TextFormatter(logging.Formatter):
    """自定义文本格式化器"""
    def format(self, record):
        # 调用父类的 format 方法获取基本格式
        log_message = super().format(record)
        return log_message

class JsonFormatter(jsonlogger.JsonFormatter):
    """自定义 JSON 格式化器，使用配置文件中的字段定义"""
    def __init__(self, fmt_params, *args, **kwargs):
        # 将配置中的字段映射拼接成字符串传递给 jsonlogger
        fmt_string = " ".join([f"%({param})s" for param in fmt_params])
        # 关键：设置 datefmt 为 None，避免 asctime 问题
        # 并设置 style='%' 以匹配 fmt_string 的格式
        super().__init__(fmt_string, datefmt=None, style='%', *args, **kwargs)

def setup_logging():
    """
    根据配置文件和 env_config 中的 RUN_ENV 设置日志系统。
    """
    # 1. 读取 YAML 配置文件
    with open(LOG_CONFIG_PATH, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)

    # 2. 从 env_config 获取运行环境 (development/production)
    run_env = env_config.RUN_ENV

    # 3. 获取环境特定配置
    env_config_section = config.get(run_env, {})
    # 合并默认配置和环境特定配置，环境特定配置优先级更高
    for key, value in env_config_section.items():
        config[key] = value

    # 4. 创建日志目录
    log_file_path = Path(config['filename'])
    log_file_path.parent.mkdir(parents=True, exist_ok=True)

    # 5. 获取日志级别
    log_level_str = config.get('level', config.get('default_level', 'INFO')).upper()
    log_level = getattr(logging, log_level_str, logging.INFO)

    # 6. 获取格式化类型
    format_type = config.get('format_type', 'text')

    # --- 关键修改点：配置 Root Logger ---
    # 获取 root logger
    root_logger = logging.getLogger() # 等同于 logging.getLogger('')
    root_logger.setLevel(log_level)

    # 清除 root logger 可能已存在的 handlers，避免重复添加
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # 8. 创建文件处理器 (RotatingFileHandler) - 为 root logger 准备
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file_path,
        maxBytes=config['max_bytes'],
        backupCount=config['backup_count'],
        encoding='utf-8' # 确保文件编码为 UTF-8
    )
    file_handler.setLevel(log_level)

    # 9. 根据格式类型设置文件处理器的格式化器 - 为 root logger 准备
    # 文件日志始终使用配置的 format_type (通常是 json)
    if format_type == 'json':
        json_fmt_params = config.get('json_format', {
            'asctime': '%(asctime)s', # 包含内置字段
            'levelname': '%(levelname)s',
            'name': '%(name)s',
            'message': '%(message)s'
        })
        file_formatter = JsonFormatter(fmt_params=list(json_fmt_params.keys()))
    else: # 默认为 text
        text_fmt_str = config.get('text_format', '[%(asctime)s] %(name)s:%(levelname)s - %(message)s')
        file_formatter = TextFormatter(fmt=text_fmt_str)

    file_handler.setFormatter(file_formatter)
    root_logger.addHandler(file_handler) # 将文件处理器添加到 root logger

    # 10. 如果环境配置要求输出到控制台，则添加控制台处理器到 root logger
    if config.get('console', False):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(log_level)

        # 控制台格式可能与文件不同
        console_format_type = config.get('console_format_type', format_type)
        if console_format_type == 'json':
            json_fmt_params = config.get('json_format', {
                'asctime': '%(asctime)s',
                'levelname': '%(levelname)s',
                'name': '%(name)s',
                'message': '%(message)s'
            })
            console_formatter = JsonFormatter(fmt_params=list(json_fmt_params.keys()))
        elif console_format_type == 'text_color':
            # 使用 colorlog 创建彩色格式化器
            import colorlog
            text_fmt_str = config.get('text_format', '[%(asctime)s] %(name)s:%(levelname)s - %(message)s')
            console_formatter = colorlog.ColoredFormatter(
                fmt=f"%(log_color)s{text_fmt_str}%(reset)s",
                datefmt=None,
                reset=True,
                log_colors={
                    'DEBUG':    'cyan',
                    'INFO':     'green',
                    'WARNING':  'yellow',
                    'ERROR':    'red',
                    'CRITICAL': 'red,bg_white',
                },
                secondary_log_colors={},
                style='%'
            )
        else: # 默认为 text
            text_fmt_str = config.get('text_format', '[%(asctime)s] %(name)s:%(levelname)s - %(message)s')
            console_formatter = TextFormatter(fmt=text_fmt_str)

        console_handler.setFormatter(console_formatter)
        root_logger.addHandler(console_handler) # 将控制台处理器添加到 root logger

    # 记录日志系统初始化成功 - 现在使用 root logger (或其子 logger)
    # 可以使用 root logger 或者一个特定的 logger，例如 "backend"
    logging.getLogger("backend").info(f"Logging system initialized. Level: {log_level_str}, Format: {format_type}, File: {log_file_path}, Console: {config.get('console', False)}")

    # root logger 级别已经在前面设置过了
    # logging.getLogger().setLevel(log_level) # 这行可以删除，因为上面已经设置了