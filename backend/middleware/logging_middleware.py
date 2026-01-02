# backend/middleware/logging_middleware.py
import logging
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
import json

logger = logging.getLogger("backend.api")

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI 中间件，用于记录 API 请求摘要。
    将请求方法、路径、状态码、处理时间、普通响应内容（文本）和异常信息整合到 message 字段中。
    对于流式响应，不记录响应体。
    根据 HTTP 状态码选择日志级别以改变控制台颜色。
    """
    async def dispatch(self, request: Request, call_next):
        """
        拦截请求，记录处理时间、状态码、普通响应内容（文本）和异常信息到日志。
        """
        start_time = time.time()

        response_status_code = 0
        response_body_str = "" # 初始化为空字符串

        try:
            # 处理请求
            response: Response = await call_next(request)
            response_status_code = response.status_code

            # --- 检查是否为流式响应 ---
            if isinstance(response, StreamingResponse):
                # 对于流式响应，不捕获 body，仅记录基本信息
                response_body_str = "<Streaming Response, Body Not Captured>"
            else:
                # --- 获取普通响应体 ---
                response_body_chunks = []
                original_body_iterator = response.body_iterator

                async def capture_body():
                    async for chunk in original_body_iterator:
                        response_body_chunks.append(chunk)
                        yield chunk

                # 重新设置 body_iterator 以允许再次读取
                response.body_iterator = capture_body()

                # 等待响应体被完全读取
                async for chunk in response.body_iterator:
                    pass # 这里实际上会执行 capture_body()

                # 重新设置 body_iterator 为原始内容
                async def original_body():
                    for chunk in response_body_chunks:
                        yield chunk
                response.body_iterator = original_body()

                response_body = b"".join(response_body_chunks)

                # --- 解码响应体 ---
                try:
                    # 尝试解码为 UTF-8
                    response_body_str = response_body.decode('utf-8')
                    # 尝试解析为 JSON，如果成功则格式化，否则保持原样
                    try:
                        parsed_json = json.loads(response_body_str)
                        response_body_str = json.dumps(parsed_json, ensure_ascii=False, indent=2) # 格式化 JSON
                    except json.JSONDecodeError:
                        # 如果不是 JSON，保持原始字符串
                        pass
                except UnicodeDecodeError:
                    # 如果解码失败，记录为字节长度
                    response_body_str = f"<{len(response_body)} bytes of non-text data>"

        except Exception as e:
            response_status_code = 500
            # 捕获异常信息
            exception_info = f"Exception: {type(e).__name__}: {e}"
            log_message = f"{request.method} {request.url.path} - {response_status_code} ({round(time.time() - start_time, 4)}s) - {exception_info}"
            logger.error(log_message) # 使用 ERROR 级别记录异常
            raise # 重新抛出异常

        # 计算处理时间
        process_time = time.time() - start_time

        # 根据状态码选择日志级别
        if 200 <= response_status_code < 300:
            log_level = logging.INFO
        elif 300 <= response_status_code < 400:
            log_level = logging.WARNING # 重定向
        elif 400 <= response_status_code < 500:
            log_level = logging.WARNING # 客户端错误
        else: # 5xx
            log_level = logging.ERROR # 服务端错误

        # 构建日志消息，包含响应内容
        log_message = f"{request.method} {request.url.path} - {response_status_code} ({round(process_time, 4)}s) - Body: {response_body_str}"

        # 使用选择的日志级别记录日志
        # colorlog 会根据 log_level 自动应用颜色
        logger.log(log_level, log_message)

        return response