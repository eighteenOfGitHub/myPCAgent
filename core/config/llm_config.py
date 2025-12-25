# core/config/llm_config.py
from typing import List, Optional, Dict, Union, Set
from pydantic import BaseModel, Field, field_validator 
from core.config.base import BaseConfig

# --- 现有的模型和路由配置 ---

class LlmPoolItem(BaseModel):
    name: str
    model: str
    type: str = Field(pattern=r"^(online|local)$")
    tags: List[str] = []
    enabled: bool = True
    api_base: Optional[str] = None
    api_key_env: Optional[str] = None
    priority: int = 0

class RoutingConfig(BaseModel):
    default_mode: str = Field(default="online", pattern=r"^(online|local)$")
    selection_strategy: str = Field(default="priority", pattern=r"^(priority)$")
    retry_on_failure: bool = True
    max_total_attempts: int = Field(default=3, ge=1)

# --- 新增：默认模型配置 ---

class DefaultModelMapping(BaseModel):
    # 键是 task_type (str)，值是不同模式下的默认模型名 (str)
    # e.g., {"general": {"online": "gpt-4o", "local": "llama3-local"}}
    #       {"coding": {"online": "gpt-4o", "local": "qwen3-local"}}
    #       {"route": {"online": "gpt-4o-mini", "local": "llama3-local"}}
    mapping: Dict[str, Dict[str, str]]

    @field_validator ('mapping')
    @classmethod
    def validate_mapping_structure(cls, v):
        """验证 mapping 的基本结构和键值类型。"""
        if not isinstance(v, dict):
            raise ValueError('The "defaults.mapping" field must be a dictionary.')
        for task_type, mode_dict in v.items():
            if not isinstance(task_type, str):
                raise ValueError(f'Task type keys in "defaults.mapping" must be strings. Found: {type(task_type)} for key {task_type}')
            if not isinstance(mode_dict, dict):
                raise ValueError(f'Value for task type "{task_type}" in "defaults.mapping" must be a dictionary {{mode: model_name}}. Found: {type(mode_dict)}')
            for mode, model_name in mode_dict.items():
                if not isinstance(mode, str):
                    raise ValueError(f'Mode keys under task type "{task_type}" must be strings. Found: {type(mode)} for key {mode}')
                if mode not in ['online', 'local']:
                    raise ValueError(f'Invalid mode "{mode}" found under task type "{task_type}" in "defaults.mapping". Valid modes are "online", "local".')
                if not isinstance(model_name, str):
                    raise ValueError(f'Model name value for task type "{task_type}", mode "{mode}" must be a string. Found: {type(model_name)}')
        return v

# --- 更新主配置类 ---

class LlmConfig(BaseConfig):
    CONFIG_FILE_NAME = "llm_config.yaml"

    llm_pool: List[LlmPoolItem]
    routing: RoutingConfig
    defaults: DefaultModelMapping 

    # --- 缓存属性 ---
    _valid_modes: Set[str] = set()
    _all_model_names: Set[str] = set()
    _all_tags: Set[str] = set()

    def __init__(self, **data):
        """Custom init to perform cross-validation after loading."""
        super().__init__(**data)
        self._valid_modes = {self.routing.default_mode}
        if self.routing.selection_strategy not in ["priority"]:
             raise ValueError(f"Unsupported selection_strategy: {self.routing.selection_strategy}")
        
        self._all_model_names = {item.name for item in self.llm_pool}
        all_tags = set()
        for item in self.llm_pool:
            all_tags.update(item.tags)
        self._all_tags = all_tags

        self._validate_defaults_against_pool()

    
    def _validate_defaults_against_pool(self):
        """Validate that default model names exist in the pool and are enabled."""
        errors = []
        for task_type, mode_dict in self.defaults.mapping.items():
            for mode, model_name in mode_dict.items():
                model_found = False
                for item in self.llm_pool:
                    if item.name == model_name:
                        model_found = True
                        if item.type != mode:
                            errors.append(
                                f'Default model "{model_name}" for task "{task_type}" in mode "{mode}" '
                                f'does not match the required model type. Model type is "{item.type}".'
                            )
                        if not item.enabled:
                             errors.append(
                                 f'Default model "{model_name}" for task "{task_type}" in mode "{mode}" is disabled.'
                             )
                        break
                
                if not model_found:
                    errors.append(
                        f'Default model "{model_name}" for task "{task_type}" in mode "{mode}" '
                        f'is not found in the llm_pool.'
                    )
        
        if errors:
            error_message = "Validation errors in llm_config.defaults.mapping:\n" + "\n".join(errors)
            raise ValueError(error_message)


    def get_default_model_name(self, task_type: str, mode: str) -> Optional[str]:
        """
        根据任务类型和模式获取默认模型名称。
        """
        return self.defaults.mapping.get(task_type, {}).get(mode, None)

    def find_model_by_name(self, name: str) -> Optional[LlmPoolItem]:
        """根据模型名称查找 LlmPoolItem 对象。"""
        for item in self.llm_pool:
            if item.name == name and item.enabled:
                return item
        return None

    def find_models_by_task_and_mode(self, task_type: str, mode: str) -> List[LlmPoolItem]:
        """根据任务类型和模式查找所有匹配的启用模型。"""
        candidates = []
        for item in self.llm_pool:
            if not item.enabled:
                continue
            if mode == "local" and item.type != "local":
                continue
            if mode == "online" and item.type != "online":
                continue
            # 支持特定任务类型或通用任务类型
            if task_type in item.tags or "general" in item.tags:
                candidates.append(item)
        if self.routing.selection_strategy == "priority":
             candidates.sort(key=lambda x: x.priority, reverse=True)
        else:
             candidates.sort(key=lambda x: x.priority, reverse=True) # Fallback
        return candidates