# backend/handlers/llm_models_setting.py

from typing import Optional


def test_new_llm_connection(
    provider: str,
    model_name: str,
    api_key: str,
    base_url: Optional[str] = None
) -> str:
    """
    Handler for 'Test Connection' button in 'Add New LLM' section.
    Returns a status message (e.g., '✅ Connection successful!').
    """
    pass


def submit_new_llm_config(
    provider: str,
    model_name: str,
    api_key: str,
    base_url: Optional[str] = None
) -> bool:
    """
    Handler for 'Submit' button to save new LLM configuration.
    Returns True if successful.
    """
    pass


def test_existing_llm_config(config_id: int) -> str:
    """
    Handler for '🟢 Test' button on an existing config row.
    Returns test result message.
    """
    pass


def delete_llm_config(config_id: int) -> bool:
    """
    Handler for '🗑️ Delete' button on an existing config row.
    Returns True if deletion succeeded.
    """
    pass