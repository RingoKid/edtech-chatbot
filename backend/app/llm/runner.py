"""Prompt runner - executes prompts against models with timing and usage tracking."""

import time
from dataclasses import dataclass

from langchain_core.messages import HumanMessage, SystemMessage

from app.llm.client import get_chat_model


@dataclass
class PromptResult:
    """Result of running a prompt against a model."""
    output: str
    latency_ms: int
    usage: dict | None = None  # Token usage if available


async def run_prompt(
    model_key: str,
    prompt: str,
    system_prompt: str | None = None,
    **model_kwargs
) -> PromptResult:
    """
    Run a prompt against a model.

    Args:
        model_key: Key from MODEL_REGISTRY
        prompt: User prompt text
        system_prompt: Optional system prompt
        **model_kwargs: Additional arguments for the model (e.g., temperature)

    Returns:
        PromptResult with output, latency, and usage info
    """
    # Get model instance
    model = get_chat_model(model_key, **model_kwargs)

    # Build messages
    messages = []
    if system_prompt:
        messages.append(SystemMessage(content=system_prompt))
    messages.append(HumanMessage(content=prompt))

    # Execute with timing
    start_time = time.perf_counter()
    response = await model.ainvoke(messages)
    end_time = time.perf_counter()

    latency_ms = int((end_time - start_time) * 1000)

    # Extract usage if available (OpenAI provides this, Gemini may not)
    usage = None
    if hasattr(response, "usage_metadata") and response.usage_metadata:
        usage = {
            "input_tokens": response.usage_metadata.get("input_tokens", 0),
            "output_tokens": response.usage_metadata.get("output_tokens", 0),
            "total_tokens": response.usage_metadata.get("total_tokens", 0),
        }
    elif hasattr(response, "response_metadata"):
        token_usage = response.response_metadata.get("token_usage", {})
        if token_usage:
            usage = {
                "input_tokens": token_usage.get("prompt_tokens", 0),
                "output_tokens": token_usage.get("completion_tokens", 0),
                "total_tokens": token_usage.get("total_tokens", 0),
            }

    return PromptResult(
        output=response.content,
        latency_ms=latency_ms,
        usage=usage,
    )
