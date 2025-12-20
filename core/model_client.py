# core/model_client.py

"""
模型客户端模块。
提供一个统一的接口来调用不同来源的大语言模型 (LLM)。

支持的后端包括：
- Ollama Client (调用本地运行的 Ollama 服务)
- API Client (调用在线模型 API，如 OpenAI, Qwen, Claude 等)
- (未来可扩展) Local Model Client

使用示例：
    # 1. 从配置创建默认客户端 (推荐)
    from core.config import get_config # 假设你有获取配置的函数
    config = get_config()
    client = ModelClientFactory.create_from_config(config)

    # 2. 或者根据模型 ID 创建特定客户端
    specific_client = ModelClientFactory.create_for_model_id(config, "openai_gpt4_turbo")

    # 3. 或者直接实例化具体客户端
    # client = OllamaClient(model="llama3.1:latest", host="http://localhost:11434")
    # client = APIClient(model="gpt-4-turbo", api_key=os.getenv("OPENAI_API_KEY"), base_url="https://api.openai.com/v1")

    response = client.chat_completion(messages=[{"role": "user", "content": "你好"}])
    print(response['choices'][0]['message']['content'])
"""

import abc
import json
import requests
import os
from typing import Dict, Any, List, Optional, Union, Generator
# 导入项目内部的日志记录器
from core.logger import get_logger  # 假设 core/logger.py 存在且按规范实现了

# --- 日志记录器 ---
# 使用 __name__ 作为 logger 名称，通常是 'core.model_client'
# 这样可以根据 logging_config.yaml 中的 loggers 配置应用 'core' 的规则
_logger = get_logger(__name__)

# --- 抽象基类 ---


class ModelClient(abc.ABC):
    """抽象基类，定义了所有模型客户端必须实现的方法。"""

    def __init__(self, model: str, **kwargs):
        """
        初始化模型客户端基础属性。

        Args:
            model (str): 要使用的具体模型标识符（名称或标签）。
            **kwargs: 其他可能需要的配置参数。
        """
        self.model = model
        self.kwargs = kwargs
        _logger.debug(
            f"Initialized ModelClient base for model '{self.model}' with kwargs: {self.kwargs}")

    @abc.abstractmethod
    def chat_completion(
            self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        执行一次非流式的对话补全请求。

        Args:
            messages (List[Dict[str, str]]): 包含对话历史的消息列表。
                                             每个消息是一个字典，包含 'role' 和 'content' 键。
            **kwargs: 传递给模型 API 的其他参数（例如 temperature, max_tokens 等）。

        Returns:
            Dict[str, Any]: 模型返回的完整响应字典。
        """
        pass

    @abc.abstractmethod
    def stream_chat_completion(
            self, messages: List[Dict[str, str]], **kwargs) -> Generator[str, None, None]:
        """
        执行一次流式的对话补全请求。

        Args:
            messages (List[Dict[str, str]]): 包含对话历史的消息列表。
                                             每个消息是一个字典，包含 'role' 和 'content' 键。
            **kwargs: 传递给模型 API 的其他参数（例如 temperature, max_tokens 等）。

        Yields:
            str: 从模型流式返回的内容片段。
        """
        pass


# --- 具体实现 ---

class OllamaClient(ModelClient):
    """用于与本地 Ollama 服务交互的客户端。"""

    def __init__(
            self,
            model: str,
            host: str = "http://localhost:11434",
            **kwargs):
        """
        初始化 Ollama 客户端。

        Args:
            model (str): Ollama 中模型的标签 (e.g., 'llama3.1:latest')。
            host (str, optional): Ollama 服务的主机地址。Defaults to "http://localhost:11434".
            **kwargs: 其他传递给父类的参数。
        """
        super().__init__(model, **kwargs)
        self.host = host.rstrip('/')
        self.chat_url = f"{self.host}/api/chat"
        _logger.info(
            f"Initialized OllamaClient for model '{self.model}' at {self.host}")

    def _make_request(self,
                      url: str,
                      payload: Dict[str,
                                    Any],
                      stream: bool = False) -> Union[Dict[str,
                                                          Any],
                                                     Generator[str,
                                                               None,
                                                               None]]:
        """
        向 Ollama API 发送请求的内部方法。

        Args:
            url (str): 请求的目标 URL。
            payload (Dict[str, Any]): 发送到 API 的 JSON 数据。
            stream (bool, optional): 是否启用流式响应。Defaults to False.

        Returns:
            Union[Dict[str, Any], Generator[str, None, None]]: 非流式返回响应字典，流式返回内容生成器。

        Raises:
            requests.exceptions.RequestException: 网络请求失败时抛出。
        """
        headers = {'Content-Type': 'application/json'}
        _logger.debug(
            f"Making request to {url} with payload: {payload} (stream={stream})")
        try:
            response = requests.post(
                url, headers=headers, json=payload, stream=stream, timeout=120)
            response.raise_for_status()
            if stream:
                def generate_stream():
                    for line in response.iter_lines():
                        if line:
                            decoded_line = line.decode('utf-8')
                            try:
                                chunk_data = json.loads(decoded_line)
                                if 'message' in chunk_data and 'content' in chunk_data['message']:
                                    content = chunk_data['message']['content']
                                    _logger.debug(
                                        f"Streaming chunk received: {content[:50]}...")  # 记录部分日志
                                    yield content
                                if chunk_data.get('done', False):
                                    _logger.debug("Stream finished.")
                                    break
                            except json.JSONDecodeError as je:
                                _logger.warning(
                                    f"Could not decode JSON line from stream: {decoded_line}. Error: {je}")
                return generate_stream()
            else:
                res_json = response.json()
                _logger.debug(f"Received non-streaming response: {res_json}")
                return res_json
        except requests.exceptions.RequestException as e:
            _logger.error(f"Ollama API request failed: {e}")
            raise

    def chat_completion(
            self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        执行 Ollama 非流式聊天完成。
        """
        payload = {"model": self.model,
                   "messages": messages, "options": kwargs}
        return self._make_request(self.chat_url, payload, stream=False)

    def stream_chat_completion(
            self, messages: List[Dict[str, str]], **kwargs) -> Generator[str, None, None]:
        """
        执行 Ollama 流式聊天完成。
        """
        payload = {"model": self.model, "messages": messages,
                   "stream": True, "options": kwargs}
        return self._make_request(self.chat_url, payload, stream=True)


class APIClient(ModelClient):
    """用于与通用 API 服务（如 OpenAI, DashScope）交互的客户端。"""

    def __init__(self, model: str, api_key: str, base_url: str, **kwargs):
        """
        初始化 API 客户端。

        Args:
            model (str): API 服务中模型的标识符 (e.g., 'gpt-4-turbo')。
            api_key (str): 用于身份验证的 API 密钥。
            base_url (str): API 服务的基础 URL (e.g., 'https://api.openai.com/v1')。
            **kwargs: 其他参数，可以包括 'headers' 等。
        """
        super().__init__(model, **kwargs)
        self.api_key = api_key
        self.base_url = base_url.rstrip('/')
        self.chat_completions_url = f"{self.base_url}/chat/completions"
        # 设置默认头部信息
        self.default_headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"}
        # 允许通过 kwargs 传入额外头部
        extra_headers = kwargs.get('headers', {})
        self.default_headers.update(extra_headers)
        _logger.info(
            f"Initialized APIClient for model '{self.model}' at {self.base_url}")

    def _make_api_request(self,
                          payload: Dict[str,
                                        Any],
                          stream: bool = False) -> Union[Dict[str,
                                                              Any],
                                                         Generator[str,
                                                                   None,
                                                                   None]]:
        """
        向 API 服务发送请求的内部方法。

        Args:
            payload (Dict[str, Any]): 发送到 API 的 JSON 数据。
            stream (bool, optional): 是否启用流式响应。Defaults to False.

        Returns:
            Union[Dict[str, Any], Generator[str, None, None]]: 非流式返回响应字典，流式返回内容生成器。

        Raises:
            requests.exceptions.RequestException: 网络请求失败时抛出。
        """
        _logger.debug(
            f"Making API request to {self.chat_completions_url} with payload: {payload} (stream={stream})")
        try:
            response = requests.post(
                self.chat_completions_url,
                headers=self.default_headers,
                json=payload,
                stream=stream,
                timeout=120)
            response.raise_for_status()
            if stream:
                def generate_stream():
                    for line in response.iter_lines():
                        if line:
                            decoded_line = line.decode('utf-8')
                            if decoded_line.startswith("data: "):
                                data_str = decoded_line[6:]
                                if data_str.strip() == "[DONE]":
                                    _logger.debug(
                                        "Stream finished (received [DONE]).")
                                    break
                                try:
                                    chunk_data = json.loads(data_str)
                                    if 'choices' in chunk_data and len(
                                            chunk_data['choices']) > 0:
                                        delta = chunk_data['choices'][0].get(
                                            'delta', {})
                                        content = delta.get('content', '')
                                        if content:
                                            _logger.debug(
                                                f"Streaming chunk received: {content[:50]}...")
                                            yield content
                                except json.JSONDecodeError as je:
                                    _logger.warning(
                                        f"Could not decode JSON line from stream: {data_str}. Error: {je}")
                return generate_stream()
            else:
                res_json = response.json()
                _logger.debug(
                    f"Received non-streaming API response: {res_json}")
                return res_json
        except requests.exceptions.RequestException as e:
            _logger.error(f"API request failed: {e}")
            try:
                error_info = response.json()
                _logger.error(f"API Error Details: {error_info}")
            except Exception as parse_error:
                _logger.warning(
                    f"Could not parse error response body: {parse_error}")
            raise

    def chat_completion(
            self, messages: List[Dict[str, str]], **kwargs) -> Dict[str, Any]:
        """
        执行 API 非流式聊天完成。
        """
        payload = {"model": self.model, "messages": messages}
        payload.update(kwargs)  # 合并额外参数
        return self._make_api_request(payload, stream=False)

    def stream_chat_completion(
            self, messages: List[Dict[str, str]], **kwargs) -> Generator[str, None, None]:
        """
        执行 API 流式聊天完成。
        """
        payload = {"model": self.model, "messages": messages, "stream": True, }
        payload.update(kwargs)  # 合并额外参数
        return self._make_api_request(payload, stream=True)


# --- 工厂类 ---

class ModelClientFactory:
    """
    工厂类，根据配置创建相应的 ModelClient 实例。
    支持从 models.available 列表中查找模型配置。
    使用 unique 'id' 来精确匹配模型和服务商组合。
    """

    @staticmethod
    def _find_model_config_by_id(
            models_config: Dict[str, Any], model_id: str) -> Optional[Dict[str, Any]]:
        """在 available 列表中根据 'id' 查找指定的模型配置。"""
        available_models = models_config.get('available', [])
        for model_cfg in available_models:
            if model_cfg.get('id') == model_id:
                _logger.debug(
                    f"Found model config for ID '{model_id}': {model_cfg}")
                return model_cfg
        _logger.warning(
            f"Model configuration for ID '{model_id}' not found in available list.")
        return None

    @staticmethod
    def create_for_model_id(
            config: Dict[str, Any], model_id: str) -> ModelClient:
        """
        根据配置和指定的模型 ID 创建 ModelClient 实例。

        Args:
            config (Dict[str, Any]): 完整的应用配置字典。
            model_id (str): 要创建客户端的模型唯一 ID。

        Returns:
            ModelClient: 对应的模型客户端实例。

        Raises:
            ValueError: 如果找不到模型配置、配置无效或缺少必要凭据。
        """
        _logger.info(f"Creating ModelClient for model ID: '{model_id}'")
        models_section = config.get('models', {})
        model_config = ModelClientFactory._find_model_config_by_id(
            models_section, model_id)

        if not model_config:
            available_ids = [m.get('id')
                             for m in models_section.get('available', [])]
            error_msg = f"Model configuration for ID '{model_id}' not found. Available IDs: {available_ids}"
            _logger.error(error_msg)
            raise ValueError(error_msg)

        provider = model_config.get('provider', '').lower()
        # 使用 model_tag (如果存在) 或 name 作为传递给客户端的具体模型标识符
        model_identifier = model_config.get(
            'model_tag', model_config.get('name'))
        _logger.debug(
            f"Resolved model identifier for '{model_id}': '{model_identifier}' (from provider '{provider}')")

        if provider == "ollama":
            host = model_config.get('base_url', "http://localhost:11434")
            _logger.info(
                f"Creating OllamaClient for model '{model_identifier}' at {host}")
            return OllamaClient(model=model_identifier, host=host)

        elif provider in ["openai", "dashscope", "api"]:  # 统一处理各种 API
            api_key_env_var = model_config.get('api_key_env_var')
            if not api_key_env_var:
                error_msg = f"'api_key_env_var' is required for API provider in model ID '{model_id}'."
                _logger.error(error_msg)
                raise ValueError(error_msg)
            api_key = os.getenv(api_key_env_var)
            if not api_key:
                error_msg = f"API key environment variable '{api_key_env_var}' is not set for model ID '{model_id}'."
                _logger.error(error_msg)
                raise ValueError(error_msg)

            base_url = model_config.get('base_url')
            if not base_url:
                error_msg = f"'base_url' is required for API provider in model ID '{model_id}'."
                _logger.error(error_msg)
                raise ValueError(error_msg)

            # 传递 headers 等额外配置 (排除已知配置项)
            extra_kwargs = {
                k: v for k,
                v in model_config.items() if k not in [
                    'id',
                    'name',
                    'model_tag',
                    'provider',
                    'api_key_env_var',
                    'base_url',
                    'capabilities']}
            _logger.info(
                f"Creating APIClient for model '{model_identifier}' at {base_url}")
            return APIClient(
                model=model_identifier,
                api_key=api_key,
                base_url=base_url,
                **extra_kwargs)

        # elif provider == "local":
        #     # ... local model logic using model_identifier ...
        #     pass

        else:
            error_msg = f"Unsupported model provider '{provider}' for model ID '{model_id}'."
            _logger.error(error_msg)
            raise ValueError(error_msg)

    @staticmethod
    def create_from_config(config: Dict[str, Any]) -> ModelClient:
        """
        根据配置中的 'models.default' (现在是一个 ID) 创建 ModelClient 实例。

        Args:
            config (Dict[str, Any]): 完整的应用配置字典。

        Returns:
            ModelClient: 默认模型的客户端实例。

        Raises:
            ValueError: 如果未设置默认模型 ID 或找不到其配置。
        """
        _logger.info("Creating default ModelClient from config.")
        models_section = config.get('models', {})
        default_model_id = models_section.get('default')

        if not default_model_id or default_model_id.lower() == 'none':
            error_msg = "Default model ID is not specified in config['models']['default']."
            _logger.error(error_msg)
            raise ValueError(error_msg)

        _logger.info(f"Default model ID resolved to: '{default_model_id}'")
        return ModelClientFactory.create_for_model_id(config, default_model_id)

# --- 使用示例 (注释掉，不包含在实际文件中) ---
#
# # config.yaml (已更新)
# # models:
# #   available:
# #     - id: ollama_qwen3_code_480b
# #       name: qwen3-code
# #       provider: ollama
# #       base_url: http://localhost:11434
# #       model_tag: qwen3-coder:480b
# #       capabilities: [code, analysis]
# #     - id: openai_gpt4_turbo
# #       name: gpt-4-turbo
# #       provider: openai
# #       api_key_env_var: OPENAI_API_KEY
# #       base_url: https://api.openai.com/v1
# #       capabilities: [text, reasoning]
# #   default: ollama_qwen3_code_480b
#
# # main.py 或 service 中
# # import os
# # os.environ['OPENAI_API_KEY'] = 'your_actual_openai_api_key' # 在运行前设置环境变量
# #
# # from core.config import load_config # 假设你有加载配置的函数
# # from core.model_client import ModelClientFactory
# #
# # config = load_config("config.yaml")
# # client = ModelClientFactory.create_from_config(config) # 使用默认模型 ID
# # # 或者
# # # client = ModelClientFactory.create_for_model_id(config, "openai_gpt4_turbo") # 使用特定模型 ID
# #
# # messages = [{"role": "user", "content": "给我讲个笑话"}]
# #
# # # 非流式调用
# # response = client.chat_completion(messages, temperature=0.7)
# # print(response['choices'][0]['message']['content'])
# #
# # # 流式调用
# # print("--- Streaming Response ---")
# # for chunk in client.stream_chat_completion(messages, temperature=0.7):
# #     print(chunk, end='', flush=True)
# # print("\n--- End of Stream ---")
