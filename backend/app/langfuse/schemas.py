"""Pydantic schemas for evaluation API requests and responses."""

from pydantic import BaseModel, Field


# --- Request Schemas ---


class CompareRequest(BaseModel):
    """Request body for POST /compare endpoint."""
    prompt: str = Field(..., description="User prompt to send to models")
    system_prompt: str | None = Field(None, description="Optional system prompt")
    models: list[str] | None = Field(
        None,
        description="Model keys to compare. Defaults to registry defaults."
    )
    criteria: list[str] | None = Field(
        None,
        description="Evaluation criteria to apply. Defaults to all."
    )
    save_to_dataset: str | None = Field(
        None,
        description="Dataset name to save results. Creates if not exists."
    )
    metadata: dict | None = Field(
        None,
        description="Additional metadata for Langfuse tracking"
    )


class CreateDatasetRequest(BaseModel):
    """Request body for POST /datasets endpoint."""
    name: str = Field(..., description="Dataset name")
    description: str | None = Field(None, description="Dataset description")


# --- Response Schemas ---


class ModelInfo(BaseModel):
    """Model information in GET /models response."""
    provider: str
    enabled: bool
    default: bool


class ModelsResponse(BaseModel):
    """Response for GET /models endpoint."""
    models: dict[str, ModelInfo]


class CriterionInfo(BaseModel):
    """Criterion information in GET /criteria response."""
    type: str
    description: str


class CriteriaResponse(BaseModel):
    """Response for GET /criteria endpoint."""
    criteria: dict[str, CriterionInfo]


class ModelResult(BaseModel):
    """Result for a single model in compare response."""
    model: str
    status: str  # "success" or "error"
    trace_id: str | None = None
    output: str | None = None
    scores: dict[str, float] | None = None
    latency_ms: int | None = None
    cost_usd: float | None = None
    error: str | None = None


class CompareResponse(BaseModel):
    """Response for POST /compare endpoint."""
    dataset_item_id: str | None = None
    comparison_id: str
    results: list[ModelResult]
    total_cost_usd: float
    langfuse_url: str | None = None


class DatasetInfo(BaseModel):
    """Dataset information in GET /datasets response."""
    name: str
    item_count: int


class DatasetsResponse(BaseModel):
    """Response for GET /datasets endpoint."""
    datasets: list[DatasetInfo]


class CreateDatasetResponse(BaseModel):
    """Response for POST /datasets endpoint."""
    name: str
    created: bool
