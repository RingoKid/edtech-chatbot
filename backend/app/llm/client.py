"""LLM client - wraps LangChain's init_chat_model for provider abstraction."""

from langchain.chat_models import init_chat_model
from langchain_core.language_models import BaseChatModel

from app.llm.config import get_model_config


def get_chat_model(model_key: str, **kwargs) -> BaseChatModel:
    """
    Get a chat model instance by model key.

    Uses LangChain's init_chat_model which handles provider differences automatically.

    Args:
        model_key: Key from MODEL_REGISTRY (e.g., "gpt-4o", "gemini-1.5-flash")
        **kwargs: Additional arguments passed to init_chat_model (e.g., temperature)

    Returns:
        BaseChatModel instance ready for invocation

    Raises:
        ValueError: If model_key is not in registry or model is disabled
    """
    config = get_model_config(model_key)

    if config is None:
        raise ValueError(f"Unknown model: {model_key}")

    if not config.enabled:
        raise ValueError(f"Model is disabled: {model_key}")

    # init_chat_model infers provider from model name for common providers
    # For explicit control, we can pass model_provider
    return init_chat_model(
        model=config.model_name,
        model_provider=config.provider,
        **kwargs
    )
