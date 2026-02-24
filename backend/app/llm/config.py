"""Model registry - defines available models and their configurations."""

from dataclasses import dataclass
from typing import Literal


@dataclass
class ModelConfig:
    """Configuration for a single model."""
    provider: Literal["openai", "google_genai"]
    model_name: str
    enabled: bool = True
    default: bool = False


# Model registry - GPT and Gemini models only
# Costs are tracked automatically by Langfuse based on model name
MODEL_REGISTRY: dict[str, ModelConfig] = {
    # OpenAI models
    "gpt-4o": ModelConfig(
        provider="openai",
        model_name="gpt-4o",
        enabled=True,
        default=True,
    ),
    "gpt-4o-mini": ModelConfig(
        provider="openai",
        model_name="gpt-4o-mini",
        enabled=True,
        default=True,
    ),
    "gpt-4-turbo": ModelConfig(
        provider="openai",
        model_name="gpt-4-turbo",
        enabled=True,
        default=False,
    ),
    "gpt-3.5-turbo": ModelConfig(
        provider="openai",
        model_name="gpt-3.5-turbo",
        enabled=True,
        default=False,
    ),
    "gpt-5.1": ModelConfig(
        provider="openai",
        model_name="gpt-5.1",
        enabled=True,
        default=False,
    ),
    "gpt-5.2": ModelConfig(
        provider="openai",
        model_name="gpt-5.2",
        enabled=True,
        default=False,
    ),
    "gpt-5.2-pro": ModelConfig(
        provider="openai",
        model_name="gpt-5.2-pro",
        enabled=True,
        default=False,
    ),
    "gpt-5.2-codex": ModelConfig(
        provider="openai",
        model_name="gpt-5.2-codex",
        enabled=True,
        default=False,
    ),
    # Google GenAI models
    "gemini-1.5-pro": ModelConfig(
        provider="google_genai",
        model_name="gemini-1.5-pro",
        enabled=True,
        default=False,
    ),
    "gemini-1.5-flash": ModelConfig(
        provider="google_genai",
        model_name="gemini-1.5-flash",
        enabled=True,
        default=False,
    ),
    "gemini-2.0-flash": ModelConfig(
        provider="google_genai",
        model_name="gemini-2.0-flash-exp",
        enabled=True,
        default=False,
    ),
}


def get_model_config(model_key: str) -> ModelConfig | None:
    """Get model configuration by key."""
    return MODEL_REGISTRY.get(model_key)


def get_default_models() -> list[str]:
    """Get list of default model keys."""
    return [key for key, config in MODEL_REGISTRY.items() if config.default]
