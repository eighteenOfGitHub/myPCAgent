# core/llm_router.py
import os
import time
from typing import List, Dict, Any, Optional
from core.config.llm_config import LLMConfig, RoutingConfig
import litellm


class LLMAgentRouter:
    def __init__(
        self,
        llm_pool: List[LLMConfig],
        routing: RoutingConfig
    ):
        """
        初始化 LLM 路由器
        
        :param llm_pool: 所有可用模型的配置列表
        :param routing: 路由策略配置
        """
        self.llm_pool = llm_pool
        self.routing = routing

    def _get_api_key(self, llm: LLMConfig) -> Optional[str]:
        if llm.api_key_env:
            return os.getenv(llm.api_key_env)
        return None

    def _call_model(self, llm: LLMConfig, messages: List[Dict], **kwargs) -> Dict[str, Any]:
        try:
            call_kwargs = {
                "model": llm.model,
                "messages": messages,
                "timeout": kwargs.get("timeout", 60),
            }
            if llm.api_base:
                call_kwargs["api_base"] = llm.api_base
            if llm.api_key_env:
                call_kwargs["api_key"] = self._get_api_key(llm)

            start = time.time()
            response = litellm.completion(**call_kwargs)
            latency = time.time() - start

            return {
                "success": True,
                "response": response,
                "latency": latency,
                "model_used": llm.name
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "model_used": llm.name
            }

    def get_response(
        self,
        messages: List[Dict],
        task_type: str = "general",
        routing_mode: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        三阶段路由：Filter → Sort → Select
        """
        mode = routing_mode or self.routing.default_mode

        # Validate mode
        if mode not in ("online", "local"):
            raise ValueError(f"无效的 routing_mode: {mode}，必须是 'online' 或 'local'")

        # ────────────────
        # Stage 1: FILTER
        # ────────────────
        candidates = []
        for llm in self.llm_pool:
            # 运行模式过滤
            if mode == "local" and llm.type != "local":
                continue
            if mode == "online" and llm.type != "online":
                # 注意：local 模型不应在 online 模式下被选中（除非你明确想允许）
                # 若需兼容，可改为 `llm.type in ("online", "hybrid")`
                continue

            # 任务类型匹配
            if task_type in llm.tags or "general" in llm.tags:
                candidates.append(llm)

        if not candidates:
            raise ValueError(f"无可用模型匹配：task_type={task_type}, mode={mode}")

        # ────────────────
        # Stage 2: SORT
        # ────────────────
        if self.routing.selection_strategy == "priority":
            candidates.sort(key=lambda x: x.priority, reverse=True)
        else:
            # 未来可扩展其他策略（如 cost、latency），目前 fallback 到 priority
            candidates.sort(key=lambda x: x.priority, reverse=True)

        # ────────────────
        # Stage 3: SELECT
        # ────────────────
        attempts = 0
        for llm in candidates:
            if attempts >= self.routing.max_total_attempts:
                break

            result = self._call_model(llm, messages, **kwargs)
            attempts += 1

            if result["success"]:
                print(f"✅ 使用模型 [{llm.name}] 完成 {task_type} 任务（第 {attempts} 次尝试）")
                return result

            if not self.routing.retry_on_failure:
                break

        raise RuntimeError(
            f"路由失败：尝试了 {attempts} 个模型（上限 {self.routing.max_total_attempts}），"
            f"task_type={task_type}, mode={mode}"
        )