"""Business logic for model comparison and evaluation."""

import asyncio
import uuid
from dataclasses import dataclass

from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type,
)

from app.llm import run_prompt, get_model_config, get_default_models, MODEL_REGISTRY
from app.langfuse.client import get_langfuse_client, flush_langfuse
from app.langfuse.criteria import run_criterion, get_available_criteria


@dataclass
class SingleModelResult:
    """Result from running a single model."""
    model: str
    status: str  # "success" or "error"
    trace_id: str | None = None
    output: str | None = None
    scores: dict[str, float] | None = None
    latency_ms: int | None = None
    cost_usd: float | None = None
    error: str | None = None


@dataclass
class CompareResult:
    """Result from comparing multiple models."""
    dataset_item_id: str | None
    comparison_id: str
    results: list[SingleModelResult]
    total_cost_usd: float
    langfuse_url: str | None


class RetryableAPIError(Exception):
    """Error that should trigger a retry (429, 5xx)."""
    pass


def _is_retryable_error(error: Exception) -> bool:
    """Check if an error should trigger a retry."""
    error_str = str(error).lower()
    return "429" in error_str or "rate limit" in error_str or "5" in error_str[:1]


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(RetryableAPIError),
)
async def _run_single_model(
    model_key: str,
    prompt: str,
    system_prompt: str | None,
    criteria: list[str],
    comparison_id: str,
    metadata: dict | None,
) -> SingleModelResult:
    """
    Run prompt against a single model with retries.

    Logs trace and scores to Langfuse using context manager API (v2+).
    """
    langfuse = get_langfuse_client()
    trace_id = None

    try:
        # Get model config for Langfuse
        model_config = get_model_config(model_key)

        # Log to Langfuse if available using context manager API
        if langfuse and model_config:
            # Create a trace span for this model run
            with langfuse.start_as_current_span(
                name=f"compare-{model_key}",
                input={"prompt": prompt, "system_prompt": system_prompt},
                metadata={
                    **(metadata or {}),
                    "model_key": model_key,
                    "comparison_id": comparison_id,
                },
            ) as span:
                # Update trace with session ID
                span.update_trace(session_id=comparison_id)
                trace_id = span.trace_id

                # Run the prompt
                result = await run_prompt(
                    model_key=model_key,
                    prompt=prompt,
                    system_prompt=system_prompt,
                )

                # Log the generation within the span
                with span.start_as_current_generation(
                    name="prompt",
                    model=model_config.model_name,
                    model_parameters={},
                    input={"system_prompt": system_prompt, "prompt": prompt},
                ) as generation:
                    generation.update(
                        output=result.output,
                        usage_details={
                            "input": result.usage.get("input_tokens", 0) if result.usage else 0,
                            "output": result.usage.get("output_tokens", 0) if result.usage else 0,
                            "total": result.usage.get("total_tokens", 0) if result.usage else 0,
                        } if result.usage else None,
                        metadata={"latency_ms": result.latency_ms},
                    )

                # Run criteria and log scores
                scores = {}
                for criterion_name in criteria:
                    eval_result = run_criterion(criterion_name, result.output)
                    if eval_result:
                        scores[criterion_name] = eval_result.score
                        span.score_trace(
                            name=criterion_name,
                            value=eval_result.score,
                            data_type="NUMERIC",
                            comment=f"Passed {eval_result.details.get('passed', 0)}/{eval_result.details.get('total', 0)} checks",
                        )

                # Update span with output
                span.update(output=result.output)

            # Cost is calculated automatically by Langfuse based on model name
            cost_usd = None

            return SingleModelResult(
                model=model_key,
                status="success",
                trace_id=trace_id,
                output=result.output,
                scores=scores,
                latency_ms=result.latency_ms,
                cost_usd=cost_usd,
            )
        else:
            # Langfuse not configured, still run prompt and criteria
            result = await run_prompt(
                model_key=model_key,
                prompt=prompt,
                system_prompt=system_prompt,
            )

            scores = {}
            for criterion_name in criteria:
                eval_result = run_criterion(criterion_name, result.output)
                if eval_result:
                    scores[criterion_name] = eval_result.score

            return SingleModelResult(
                model=model_key,
                status="success",
                trace_id=None,
                output=result.output,
                scores=scores,
                latency_ms=result.latency_ms,
                cost_usd=None,
            )

    except Exception as e:
        # Check if retryable
        if _is_retryable_error(e):
            raise RetryableAPIError(str(e)) from e

        return SingleModelResult(
            model=model_key,
            status="error",
            trace_id=trace_id,
            error=str(e),
        )


async def compare_models(
    prompt: str,
    system_prompt: str | None = None,
    models: list[str] | None = None,
    criteria: list[str] | None = None,
    save_to_dataset: str | None = None,
    metadata: dict | None = None,
) -> CompareResult:
    """
    Run prompt against multiple models and evaluate outputs.

    Args:
        prompt: User prompt text
        system_prompt: Optional system prompt
        models: List of model keys (defaults to registry defaults)
        criteria: List of criteria to apply (defaults to all)
        save_to_dataset: Optional dataset name to save results
        metadata: Optional metadata for Langfuse tracking

    Returns:
        CompareResult with all model results
    """
    # Get defaults
    if models is None:
        models = get_default_models()

    if criteria is None:
        criteria = list(get_available_criteria().keys())

    # Validate models exist
    for model_key in models:
        if model_key not in MODEL_REGISTRY:
            raise ValueError(f"Unknown model: {model_key}")

    # Generate comparison ID
    comparison_id = f"cmp-{uuid.uuid4().hex[:12]}"

    langfuse = get_langfuse_client()
    dataset_item_id = None

    # Create dataset item if requested
    if save_to_dataset and langfuse:
        try:
            # Create dataset if it doesn't exist (Langfuse handles this)
            langfuse.create_dataset(name=save_to_dataset)
        except Exception:
            # Dataset might already exist, that's fine
            pass

        # Create dataset item
        item = langfuse.create_dataset_item(
            dataset_name=save_to_dataset,
            input={
                "prompt": prompt,
                "system_prompt": system_prompt,
            },
            metadata={
                **(metadata or {}),
                "comparison_id": comparison_id,
                "models": models,
            },
        )
        dataset_item_id = item.id

    # Run all models in parallel
    tasks = [
        _run_single_model(
            model_key=model_key,
            prompt=prompt,
            system_prompt=system_prompt,
            criteria=criteria,
            comparison_id=comparison_id,
            metadata=metadata,
        )
        for model_key in models
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    # Convert exceptions to error results
    processed_results: list[SingleModelResult] = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            processed_results.append(SingleModelResult(
                model=models[i],
                status="error",
                error=str(result),
            ))
        else:
            processed_results.append(result)

    # Calculate total cost
    total_cost = sum(
        r.cost_usd for r in processed_results
        if r.cost_usd is not None
    )

    # Flush Langfuse events
    flush_langfuse()

    # Build Langfuse URL
    langfuse_url = None
    if langfuse:
        config = langfuse._client_wrapper._public_key[:8] if hasattr(langfuse, '_client_wrapper') else ""
        langfuse_url = f"https://cloud.langfuse.com/sessions/{comparison_id}"

    return CompareResult(
        dataset_item_id=dataset_item_id,
        comparison_id=comparison_id,
        results=processed_results,
        total_cost_usd=total_cost,
        langfuse_url=langfuse_url,
    )


async def list_datasets() -> list[dict]:
    """List all datasets from Langfuse."""
    langfuse = get_langfuse_client()
    if not langfuse:
        return []

    try:
        # Langfuse SDK provides get_datasets() method
        datasets = langfuse.get_datasets()
        return [
            {
                "name": d.name,
                "item_count": len(d.items) if hasattr(d, 'items') else 0,
            }
            for d in datasets.data
        ] if hasattr(datasets, 'data') else []
    except Exception:
        return []


async def create_dataset(name: str, description: str | None = None) -> dict:
    """Create a new dataset in Langfuse."""
    langfuse = get_langfuse_client()
    if not langfuse:
        return {"name": name, "created": False}

    try:
        langfuse.create_dataset(name=name, description=description)
        return {"name": name, "created": True}
    except Exception:
        # Dataset might already exist
        return {"name": name, "created": False}
