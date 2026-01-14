"""API endpoints for model comparison and evaluation."""

from fastapi import APIRouter, HTTPException

from app.llm import MODEL_REGISTRY
from app.langfuse.criteria import get_available_criteria
from app.langfuse.schemas import (
    CompareRequest,
    CompareResponse,
    CreateDatasetRequest,
    CreateDatasetResponse,
    CriteriaResponse,
    CriterionInfo,
    DatasetInfo,
    DatasetsResponse,
    ModelInfo,
    ModelResult,
    ModelsResponse,
)
from app.langfuse.service import compare_models, list_datasets, create_dataset


router = APIRouter(prefix="/evals", tags=["evals"])


@router.get("/models", response_model=ModelsResponse)
async def get_models():
    """List available models from the registry."""
    models = {
        key: ModelInfo(
            provider=config.provider,
            enabled=config.enabled,
            default=config.default,
        )
        for key, config in MODEL_REGISTRY.items()
    }
    return ModelsResponse(models=models)


@router.get("/criteria", response_model=CriteriaResponse)
async def get_criteria():
    """List available evaluation criteria."""
    criteria_raw = get_available_criteria()
    criteria = {
        name: CriterionInfo(
            type=info["type"],
            description=info["description"],
        )
        for name, info in criteria_raw.items()
    }
    return CriteriaResponse(criteria=criteria)


@router.post("/compare", response_model=CompareResponse)
async def compare(request: CompareRequest):
    """
    Run prompt against multiple models and evaluate outputs.

    Returns results for all models, even if some fail.
    """
    try:
        result = await compare_models(
            prompt=request.prompt,
            system_prompt=request.system_prompt,
            models=request.models,
            criteria=request.criteria,
            save_to_dataset=request.save_to_dataset,
            metadata=request.metadata,
        )

        return CompareResponse(
            dataset_item_id=result.dataset_item_id,
            comparison_id=result.comparison_id,
            results=[
                ModelResult(
                    model=r.model,
                    status=r.status,
                    trace_id=r.trace_id,
                    output=r.output,
                    scores=r.scores,
                    latency_ms=r.latency_ms,
                    cost_usd=r.cost_usd,
                    error=r.error,
                )
                for r in result.results
            ],
            total_cost_usd=result.total_cost_usd,
            langfuse_url=result.langfuse_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/datasets", response_model=DatasetsResponse)
async def get_datasets():
    """List existing datasets."""
    datasets = await list_datasets()
    return DatasetsResponse(
        datasets=[
            DatasetInfo(name=d["name"], item_count=d["item_count"])
            for d in datasets
        ]
    )


@router.post("/datasets", response_model=CreateDatasetResponse)
async def create_dataset_endpoint(request: CreateDatasetRequest):
    """Create a new empty dataset."""
    result = await create_dataset(
        name=request.name,
        description=request.description,
    )
    return CreateDatasetResponse(
        name=result["name"],
        created=result["created"],
    )
