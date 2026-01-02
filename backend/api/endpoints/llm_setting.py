# backend/middleware/logging_middleware.py
import logging
import time
from fastapi import Request, Response
from fastapi.exceptions import HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import StreamingResponse
from pydantic import BaseModel
from typing import Union
import json

logger = logging.getLogger("backend.api")

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    FastAPI 中间件，用于记录 API 请求摘要。
    记录请求方法、路径、状态码、处理时间，以及响应内容的类型或异常详情。
    根据 HTTP 状态码选择日志级别以改变控制台颜色。
    """
    async def dispatch(self, request: Request, call_next):
        """
        拦截请求，记录处理时间、状态码、响应内容类型或异常详情到日志。
        """
        start_time = time.time()

        response: Union[Response, None] = None
        response_status_code = 0
        content_info = ""

        try:
            response = await call_next(request)
            response_status_code = response.status_code

            # 暂时不处理流式响应
            if isinstance(response, StreamingResponse):
                content_info = f"Streaming Response (Status: {response_status_code})"
            else:
                response_body_chunks = []
                original_body_iterator = response.body_iterator

                async def capture_body():
                    async for chunk in original_body_iterator:
                        response_body_chunks.append(chunk)
                        yield chunk

                response.body_iterator = capture_body()

                async for chunk in response.body_iterator:
                    pass

                async def original_body():
                    for chunk in response_body_chunks:
                        yield chunk
                response.body_iterator = original_body()

                response_body = b"".join(response_body_chunks)

                try:
                    decoded_body = response_body.decode('utf-8')
                    parsed_content = json.loads(decoded_body)

                    # 根据不同类型的响应内容进行不同的处理
                    if isinstance(parsed_content, dict):
                        content_info = f"Dict Response (Status: {response_status_code})"
                    elif isinstance(parsed_content, list):
                        content_info = f"List Response (Status: {response_status_code})"
                    else:
                        if isinstance(parsed_content, (str, int, float, bool)):
                             content_info = f"Primitive Value Response: {parsed_content} (Type: {type(parsed_content).__name__}, Status: {response_status_code})"
                        else:
                            content_info = f"Other JSON Type Response: {type(parsed_content).__name__} (Status: {response_status_code})"

                except (UnicodeDecodeError, json.JSONDecodeError) as e:
                    try:
                        decoded_body = response_body.decode('utf-8')
                        content_info = f"Plain Text Response: {decoded_body[:100]}{'...' if len(decoded_body) > 100 else ''} (Status: {response_status_code})"
                    except UnicodeDecodeError:
                        content_info = f"Binary Response ({len(response_body)} bytes, Status: {response_status_code})"

        except HTTPException as e:
            response_status_code = e.status_code
            content_info = f"HTTPException: {e.detail} (Status: {e.status_code})"
        except Exception as e:
            response_status_code = 500
            content_info = f"Unhandled Exception: {type(e).__name__}: {e}"
            logger.error(content_info, exc_info=True)
            raise

        process_time = time.time() - start_time

        if 200 <= response_status_code < 300:
            log_level = logging.INFO
        elif 300 <= response_status_code < 400:
            log_level = logging.WARNING
        elif 400 <= response_status_code < 500:
            log_level = logging.WARNING
        else:
            log_level = logging.ERROR

        log_message = f"{request.method} {request.url.path} - {response_status_code} ({round(process_time, 4)}s) - {content_info}"

        logger.log(log_level, log_message)

        return response