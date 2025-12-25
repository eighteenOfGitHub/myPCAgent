# core/llm_router.py
"""LLM 路由模块。提供一个 LLMAgentRouter 类来管理和路由 LLM 调用。"""

import os
import time
import asyncio
from typing import List, Dict, Any, Optional, Union, AsyncGenerator
import logging

from core.config.llm_config import LlmPoolItem, RoutingConfig, LlmConfig

import litellm


class LLMAgentRouter:
    """
    LLM 路由器，负责根据配置和策略选择合适的模型进行调用。
    - 默认模型基于 task_type 和初始化时固定的 routing_mode。
    - 提供统一入口，通过参数区分同步/异步、流式/非流式。
    - 故障转移逻辑集成在主调用流程中。
    Logger 在初始化时传入。
    """

    def __init__(
        self,
        llm_config: LlmConfig,
        logger: logging.Logger
    ):
        """
        初始化 LLM 路由器。

        :param llm_config: 完整的 LLM 配置对象 (LlmConfig)。
        :param logger: logger 实例，用于记录日志。
        """
        self.llm_config = llm_config
        self.mode = llm_config.routing.default_mode
        self.logger = logger
        
        # --- 预处理：构建默认模型映射 ---
        self._default_model_map: Dict[str, LlmPoolItem] = {}
        for task_type, mode_dict in llm_config.defaults.mapping.items():
            model_name = mode_dict.get(self.mode)
            if model_name:
                model_item = llm_config.find_model_by_name(model_name)
                if model_item:
                    self._default_model_map[task_type] = model_item
                    self.logger.debug(f"Mapped default model for task '{task_type}': '{model_name}'")
                else:
                    self.logger.warning(f"Default model '{model_name}' for task '{task_type}' in mode '{self.mode}' not found/enabled in pool.")
            else:
                 self.logger.debug(f"No default model specified for task '{task_type}' in mode '{self.mode}'.")

        self.logger.info(f"LLMAgentRouter initialized for mode '{self.mode}' with {len(self._default_model_map)} default mappings.")


    def _get_api_key(self, llm: LlmPoolItem) -> Optional[str]:
        """获取模型的 API Key。"""
        if llm.api_key_env:
            key = os.getenv(llm.api_key_env)
            if not key:
                self.logger.debug(f"API Key env var '{llm.api_key_env}' not set for model '{llm.name}'.")
            return key
        return None

    def _prepare_call_kwargs(self, llm: LlmPoolItem, messages: List[Dict], stream: bool, **kwargs) -> Dict[str, Any]:
        """准备调用 LLM 所需的参数字典。"""
        call_kwargs = {
            "model": llm.model,
            "messages": messages,
            "stream": stream,
            # 利用 litellm 内置重试
            "num_retries": self.llm_config.routing.max_total_attempts - 1,
            "request_timeout": kwargs.get("timeout", 60),
        }
        if llm.api_base:
            call_kwargs["api_base"] = llm.api_base
        api_key = self._get_api_key(llm)
        if api_key:
             call_kwargs["api_key"] = api_key
        return call_kwargs

    def _call_model_sync(self, llm: LlmPoolItem, messages: List[Dict], stream: bool = False, **kwargs) -> Any:
        """同步调用单个 LLM 模型。"""
        call_kwargs = self._prepare_call_kwargs(llm, messages, stream, **kwargs)
        self.logger.debug(f"Sync calling model '{llm.name}' ({llm.model}) with args: {call_kwargs}")
        start = time.monotonic()
        try:
            response = litellm.completion(**call_kwargs)
            latency = time.monotonic() - start
            self.logger.debug(f"Sync model '{llm.name}' responded in {latency:.3f}s.")
            return response
        except Exception as e:
            latency = time.monotonic() - start
            error_msg = f"Sync call to model '{llm.name}' failed after internal retries and {latency:.3f}s: {e}"
            self.logger.error(error_msg)
            raise

    async def _call_model_async(self, llm: LlmPoolItem, messages: List[Dict], stream: bool = False, **kwargs) -> Any:
        """异步调用单个 LLM 模型。"""
        call_kwargs = self._prepare_call_kwargs(llm, messages, stream, **kwargs)
        self.logger.debug(f"Async calling model '{llm.name}' ({llm.model}) with args: {call_kwargs}")
        start = time.monotonic()
        try:
            response = await litellm.acompletion(**call_kwargs) 
            latency = time.monotonic() - start
            self.logger.debug(f"Async model '{llm.name}' responded in {latency:.3f}s.")
            return response
        except Exception as e:
            latency = time.monotonic() - start
            error_msg = f"Async call to model '{llm.name}' failed after internal retries and {latency:.3f}s: {e}"
            self.logger.error(error_msg)
            raise

    def _attempt_call_with_fallback(
        self, 
        initial_model: LlmPoolItem, 
        messages: List[Dict], 
        task_type: str, 
        stream: bool, 
        is_async: bool, 
        **kwargs
    ) -> Any:
        """
        (同步) 尝试调用模型，如果失败则根据任务类型和模式寻找备选模型并重试。
        """
        # 确保同步路径不能被异步调用意外触发
        if is_async:
            raise RuntimeError("_attempt_call_with_fallback (sync) cannot handle async calls. Use _aattempt_call_with_fallback.")

        attempts_made = 0
        current_model = initial_model
        tried_models_log = []

        while attempts_made < self.llm_config.routing.max_total_attempts:
            attempts_made += 1
            tried_models_log.append(current_model.name)
            self.logger.info(f"[Attempt {attempts_made}/{self.llm_config.routing.max_total_attempts}] Calling model '{current_model.name}' for task '{task_type}' (stream={stream}, async={is_async})...")
            
            try:
                response = self._call_model_sync(current_model, messages, stream=stream, **kwargs)
                self.logger.info(f"✅ Success on attempt {attempts_made} using model '{current_model.name}' for task '{task_type}'.")
                return response
                    
            except Exception as e:
                self.logger.warning(f"❌ Attempt {attempts_made} with model '{current_model.name}' failed: {e}")

                if not self.llm_config.routing.retry_on_failure or attempts_made >= self.llm_config.routing.max_total_attempts:
                    break
                
                # --- Select Fallback Model ---
                candidates = self.llm_config.find_models_by_task_and_mode(task_type, self.mode)
                available_candidates = [c for c in candidates if c.name not in tried_models_log]

                if not available_candidates:
                    self.logger.error(f"No untried fallback models left for task '{task_type}' in mode '{self.mode}'. Tried: {tried_models_log}")
                    raise RuntimeError(f"All models for task '{task_type}' failed or exhausted. Last error: {e}") from e
                
                next_model = available_candidates[0]
                self.logger.info(f"Selecting fallback model '{next_model.name}' (priority {next_model.priority}).")
                current_model = next_model
        
        final_error_msg = f"Exhausted max attempts ({self.llm_config.routing.max_total_attempts}) for task '{task_type}'. Tried models: {tried_models_log}."
        self.logger.error(final_error_msg)
        raise RuntimeError(final_error_msg)


    async def _attempt_call_with_fallback(
        self, 
        initial_model: LlmPoolItem, 
        messages: List[Dict], 
        task_type: str, 
        stream: bool, 
        **kwargs
    ) -> Any:
        """
        (异步) 尝试调用模型，如果失败则根据任务类型和模式寻找备选模型并重试。
        """
        attempts_made = 0
        current_model = initial_model
        tried_models_log = []

        while attempts_made < self.llm_config.routing.max_total_attempts:
            attempts_made += 1
            tried_models_log.append(current_model.name)
            self.logger.info(f"[Attempt {attempts_made}/{self.llm_config.routing.max_total_attempts}] Async calling model '{current_model.name}' for task '{task_type}' (stream={stream})...")
            
            try:
                response = await self._call_model_async(current_model, messages, stream=stream, **kwargs)
                self.logger.info(f"✅ Async success on attempt {attempts_made} using model '{current_model.name}' for task '{task_type}'.")
                return response
                    
            except Exception as e:
                self.logger.warning(f"❌ Async attempt {attempts_made} with model '{current_model.name}' failed: {e}")

                if not self.llm_config.routing.retry_on_failure or attempts_made >= self.llm_config.routing.max_total_attempts:
                    break
                
                # --- Select Fallback Model ---
                candidates = self.llm_config.find_models_by_task_and_mode(task_type, self.mode)
                available_candidates = [c for c in candidates if c.name not in tried_models_log]

                if not available_candidates:
                    self.logger.error(f"No untried async fallback models left for task '{task_type}' in mode '{self.mode}'. Tried: {tried_models_log}")
                    raise RuntimeError(f"All async models for task '{task_type}' failed or exhausted. Last error: {e}") from e
                
                next_model = available_candidates[0]
                self.logger.info(f"Selecting async fallback model '{next_model.name}' (priority {next_model.priority}).")
                current_model = next_model
        
        final_error_msg = f"Async: Exhausted max attempts ({self.llm_config.routing.max_total_attempts}) for task '{task_type}'. Tried models: {tried_models_log}."
        self.logger.error(final_error_msg)
        raise RuntimeError(final_error_msg)


    # --- 主要对外接口 ---

    def get_response(
        self, 
        messages: List[Dict], 
        task_type: str = "general", 
        stream: bool = False, 
        is_async: bool = False,
        **kwargs
    ) -> Union[Dict[str, Any], Any, AsyncGenerator[Any, None]]:
        """
        获取 LLM 响应。

        :param messages: 消息列表。
        :param task_type: 任务类型 ('general', 'coding', 'route', ...)，用于查找默认模型。
        :param stream: 是否流式输出。
        :param is_async: 是否异步调用。
        :param kwargs: 其他传递给 litellm.completion/acompletion 的参数。
        :return: 
            - 同步非流式: LLM 响应字典。
            - 同步流式: 流式响应对象 (生成器等)。
            - 异步非流式: Awaitable 返回 LLM 响应字典。
            - 异步流式: Awaitable 返回 AsyncGenerator。
        """
        # --- 核心变更：支持 'route' 任务类型 ---
        # 优先检查是否存在为 'route' 任务类型配置的默认模型
        if task_type == "route":
            model = self._default_model_map.get("route")
            log_task_desc = "routing decision (task_type='route')"
        else:
            # 对于其他任务类型，按原样查找
            model = self._default_model_map.get(task_type)
            log_task_desc = f"task '{task_type}'"

        if not model:
            error_msg = f"No default model configured for {log_task_desc} in mode '{self.mode}'."
            self.logger.error(error_msg)
            raise ValueError(error_msg)

        self.logger.info(f"Using default model '{model.name}' for {log_task_desc} (stream={stream}, async={is_async}).")

        if is_async:
            return self._aattempt_call_with_fallback(model, messages, task_type, stream, **kwargs)
        else:
            return self._attempt_call_with_fallback(model, messages, task_type, stream, is_async, **kwargs)
        


