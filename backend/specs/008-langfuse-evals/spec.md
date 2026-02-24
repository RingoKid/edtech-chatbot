# 008: Langfuse Evaluation System

## Overview

**Version:** 0.1 — Multi-model comparison with structural evaluation
**Status:** Implemented
**Last Updated:** 2026-01-13

Backend APIs for running prompts against multiple models and evaluating outputs. Uses Langfuse Cloud for experiment tracking and cost calculation.

**Scope:** Model runner + Compare API + Langfuse integration + Dataset auto-save

---

## Documentation Sources (REQUIRED)

Before implementing, use Context7 MCP to look up current documentation:

| Library | Topics to Query |
|---------|-----------------|
| `langfuse` | Python SDK, traces, scores, datasets, create_dataset_item, cost tracking |
| `langchain` | init_chat_model, BaseChatModel, Google GenAI, async invoke |
| `fastapi` | APIRouter, async endpoints, Pydantic models |

Do NOT implement from memory. Fetch current docs.

---

## Architecture

### Module Structure

```
backend/app/
├── llm/                          # Shared LLM infrastructure
│   ├── __init__.py
│   ├── config.py                 # Model registry
│   ├── client.py                 # init_chat_model wrapper
│   └── runner.py                 # run_prompt() function
│
└── langfuse/                     # Evaluation module (isolated)
    ├── __init__.py
    ├── config.py                 # Langfuse settings
    ├── client.py                 # Langfuse SDK singleton
    ├── criteria.py               # Eval criteria (structure_complete)
    ├── schemas.py                # API request/response models
    ├── service.py                # Business logic
    └── router.py                 # API endpoints
```

### Dependency Flow

```
router.py → service.py → llm/runner.py → llm/client.py
                      → client.py (Langfuse)
                      → criteria.py
```

---

## Model Registry

GPT and Gemini models only. Costs tracked automatically by Langfuse.

| Model Key | Provider | Model Name | Default |
|-----------|----------|------------|---------|
| `gpt-4o` | openai | gpt-4o | Yes |
| `gpt-4o-mini` | openai | gpt-4o-mini | Yes |
| `gpt-4-turbo` | openai | gpt-4-turbo | No |
| `gpt-3.5-turbo` | openai | gpt-3.5-turbo | No |
| `gemini-1.5-pro` | google_genai | gemini-1.5-pro | No |
| `gemini-1.5-flash` | google_genai | gemini-1.5-flash | No |
| `gemini-2.0-flash` | google_genai | gemini-2.0-flash-exp | No |

Use LangChain's `init_chat_model` which handles provider differences automatically.

---

## API Endpoints

Base path: `/api/v1/evals`

No authentication required.

### GET /models

List available models from registry.

**Response:**
```json
{
  "models": {
    "gpt-4o": {"provider": "openai", "enabled": true, "default": true},
    "gemini-1.5-flash": {"provider": "google_genai", "enabled": true, "default": false}
  }
}
```

### GET /criteria

List available evaluation criteria.

**Response:**
```json
{
  "criteria": {
    "structure_complete": {
      "type": "rule-based",
      "description": "Checks if lesson has all required sections and markers"
    }
  }
}
```

### POST /compare

Main endpoint. Runs prompt against models, evaluates, saves to dataset.

**Request:**
```json
{
  "prompt": "Create a handwriting lesson for letter A, PreK level",
  "system_prompt": "You are a structured literacy curriculum expert...",
  "models": ["gpt-4o", "gpt-4o-mini", "gemini-1.5-flash"],
  "criteria": ["structure_complete"],
  "save_to_dataset": "handwriting-lessons",
  "metadata": {
    "workflow_version": "1.1",
    "workflow_file": "lesson-generator-v01.json",
    "grade": "PreK",
    "letter": "A"
  }
}
```

| Field | Type | Required | Notes |
|-------|------|----------|-------|
| `prompt` | string | Yes | User prompt |
| `system_prompt` | string | No | System prompt |
| `models` | array | No | Model keys. Defaults to registry defaults |
| `criteria` | array | No | Eval criteria. Defaults to all |
| `save_to_dataset` | string | No | Dataset name. Creates if not exists |
| `metadata` | object | No | Tracked in Langfuse (workflow version, etc.) |

**Response:**
```json
{
  "dataset_item_id": "item-xyz",
  "comparison_id": "cmp-abc123",
  "results": [
    {
      "model": "gpt-4o",
      "status": "success",
      "trace_id": "trace-xyz",
      "output": "# Handwriting Lesson...",
      "scores": {"structure_complete": 0.92},
      "latency_ms": 1240,
      "cost_usd": 0.003
    },
    {
      "model": "gemini-1.5-flash",
      "status": "success",
      "trace_id": "trace-abc",
      "output": "# Letter A Lesson...",
      "scores": {"structure_complete": 0.88},
      "latency_ms": 650,
      "cost_usd": 0.0001
    }
  ],
  "total_cost_usd": 0.0031,
  "langfuse_url": "https://cloud.langfuse.com/project/.../sessions/cmp-abc123"
}
```

### GET /datasets

List existing datasets.

**Response:**
```json
{
  "datasets": [
    {"name": "handwriting-lessons", "item_count": 12},
    {"name": "vocabulary-lessons", "item_count": 5}
  ]
}
```

### POST /datasets

Create empty dataset explicitly.

**Request:**
```json
{
  "name": "handwriting-lessons",
  "description": "Test cases for handwriting lesson generation"
}
```

---

## Core Logic

### run_prompt() Function

Location: `app/llm/runner.py`

Uses LangChain's `init_chat_model` for provider abstraction.

**Behavior:**
1. Get model config from registry
2. Initialize model via `init_chat_model(model_name)`
3. Build messages (system + user)
4. Execute async with timing
5. Return output, latency, token usage

**Future:** Add optional `output_schema` parameter for structured output.

### compare_models() Function

Location: `app/langfuse/service.py`

**Behavior:**
1. If `save_to_dataset` provided, create dataset item
2. Run all models in parallel using `asyncio.gather`
3. For each result, run eval criteria
4. Log trace + scores to Langfuse
5. Link traces to dataset item
6. Return aggregated results

### Langfuse Cost Tracking

Langfuse automatically calculates costs when you provide:
- Model name in trace
- Token usage metadata

No manual price lookup needed.

---

## Evaluation Criteria

### structure_complete (Rule-based)

Checks if lesson output contains required sections and markers.

**Required Sections:**
- Standards
- Objectives
- Materials
- Review & Connect
- Model, Explain & Engage
- Guided Practice
- Application
- Wrap-Up

**Required Markers:**
| Marker | Pattern | Purpose |
|--------|---------|---------|
| Explanation | `[...]` | AI explains lesson parts |
| Teacher Script | `#` | What teacher says |
| Child Response | `(...)` | Expected responses |
| Teacher Does | `{...}` | Teacher actions |
| Gesture | `+` | Phoneme gesture |
| Verbal Cues | `##` | Letter formation |
| Modification | `*` | End-of-lesson prompt |

**Scoring:** `passed_checks / total_checks` (0.0 to 1.0)

**Implementation:** Pure Python string matching. No LLM call.

---

## Error Handling

### Partial Results

If one model fails, return results for successful models:

```json
{
  "results": [
    {"model": "gpt-4o", "status": "success", ...},
    {"model": "gemini-1.5-flash", "status": "error", "error": "API timeout", "trace_id": null}
  ]
}
```

### Retry Logic

Use tenacity library:
- Max 2 retries
- Exponential backoff
- Retry on 429 and 5xx only

---

## Files to Create

| Path | Purpose |
|------|---------|
| `app/llm/__init__.py` | Module exports |
| `app/llm/config.py` | Model registry |
| `app/llm/client.py` | init_chat_model wrapper |
| `app/llm/runner.py` | run_prompt() function |
| `app/langfuse/__init__.py` | Module exports |
| `app/langfuse/config.py` | Langfuse settings (reads env vars) |
| `app/langfuse/client.py` | Langfuse SDK singleton |
| `app/langfuse/criteria.py` | structure_complete evaluator |
| `app/langfuse/schemas.py` | Pydantic request/response models |
| `app/langfuse/service.py` | compare_models(), dataset logic |
| `app/langfuse/router.py` | API endpoints |

---

## Wiring

In `app/main.py`:

```python
from app.langfuse.router import router as evals_router

public_router.include_router(evals_router)  # /api/v1/evals/*
```

---

## Testing

### Verify Models Endpoint

```bash
curl http://localhost:8000/api/v1/evals/models
```

### Verify Compare Endpoint

```bash
curl -X POST http://localhost:8000/api/v1/evals/compare \
  -H "Content-Type: application/json" \
  -d '{
    "prompt": "Create a handwriting lesson for letter A, PreK",
    "models": ["gpt-4o-mini"],
    "criteria": ["structure_complete"],
    "metadata": {"test": true}
  }'
```

### Verification Checklist

- [ ] `GET /evals/models` returns registry
- [ ] `GET /evals/criteria` returns available criteria
- [ ] `POST /evals/compare` runs prompt against models
- [ ] `POST /evals/compare` with `save_to_dataset` creates dataset item
- [ ] Scores calculated correctly for structure_complete
- [ ] Traces visible in Langfuse Cloud
- [ ] Costs calculated automatically by Langfuse
- [ ] Partial results returned on model failure

---

## Storage Summary

| What | Where |
|------|-------|
| n8n workflows | Git: `n8n/workflows/*.json` |
| Prompts | Generated by n8n, saved to Langfuse datasets |
| Datasets | Langfuse Cloud |
| Model outputs | Langfuse Cloud (traces) |
| Eval scores | Langfuse Cloud (scores) |
| Costs | Langfuse Cloud (automatic) |

---

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| LLM module (`app/llm/*`) | ✅ Done | Model registry, client, runner |
| Langfuse module (`app/langfuse/*`) | ✅ Done | Config, client, criteria, schemas, service, router |
| GET /evals/models | ✅ Done | Returns all registered models |
| GET /evals/criteria | ✅ Done | Returns structure_complete criterion |
| POST /evals/compare | ✅ Done | Runs models in parallel, scores, logs to Langfuse |
| GET /evals/datasets | ✅ Done | Lists Langfuse datasets |
| POST /evals/datasets | ✅ Done | Creates new dataset |
| structure_complete evaluator | ✅ Done | Rule-based section/marker checker |
| Langfuse tracing | ✅ Done | Uses v2 context manager API |
| Retry logic | ✅ Done | tenacity with exponential backoff |
| n8n workflow v02 | ✅ Done | Uses /api/v1/evals/compare endpoint |

---

## Implementation Files

| File | Purpose |
|------|---------|
| `app/llm/__init__.py` | Module exports |
| `app/llm/config.py` | Model registry with 7 models (OpenAI + Gemini) |
| `app/llm/client.py` | `get_chat_model()` wrapper around init_chat_model |
| `app/llm/runner.py` | `run_prompt()` async function with timing |
| `app/langfuse/__init__.py` | Module exports |
| `app/langfuse/config.py` | Langfuse settings from env vars |
| `app/langfuse/client.py` | Langfuse SDK singleton |
| `app/langfuse/criteria.py` | `structure_complete` evaluator |
| `app/langfuse/schemas.py` | Pydantic request/response models |
| `app/langfuse/service.py` | `compare_models()`, dataset functions |
| `app/langfuse/router.py` | FastAPI endpoints |
| `app/main.py` | Router wiring (line 9, 39) |
| `n8n/workflows/lesson-generator-v02.json` | n8n workflow with Langfuse integration |

---

## Verification

### Manual Tests

**GET /evals/models**
```bash
curl http://localhost:8000/api/v1/evals/models
```
Expected: Returns JSON with 7 models (gpt-4o, gpt-4o-mini, gpt-4-turbo, gpt-3.5-turbo, gemini-1.5-pro, gemini-1.5-flash, gemini-2.0-flash)

**GET /evals/criteria**
```bash
curl http://localhost:8000/api/v1/evals/criteria
```
Expected: Returns `{"criteria": {"structure_complete": {...}}}`

**POST /evals/compare**
```bash
curl -X POST "http://localhost:8000/api/v1/evals/compare" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a lesson for letter A", "models": ["gpt-4o-mini"], "criteria": ["structure_complete"]}'
```
Expected: Returns comparison result with trace_id, output, scores, latency_ms

**POST /evals/compare with dataset save**
```bash
curl -X POST "http://localhost:8000/api/v1/evals/compare" \
  -H "Content-Type: application/json" \
  -d '{"prompt": "Create a lesson", "models": ["gpt-4o-mini"], "save_to_dataset": "test-dataset"}'
```
Expected: Returns result with `dataset_item_id` populated

**n8n Workflow v02 (after deployment)**
```bash
# 1. Deploy workflow to n8n
./n8n/api.sh workflows -X POST -H "Content-Type: application/json" \
  -d @n8n/workflows/lesson-generator-v02.json

# 2. Activate workflow (replace {id} with returned workflow ID)
./n8n/api.sh workflows/{id}/activate -X POST

# 3. Test webhook endpoint
curl -X POST http://localhost:5678/webhook/generate-v2 \
  -H "Content-Type: application/json" \
  -d '{"grade": "PreK", "letter": "A"}'
```
Expected: Returns JSON with `comparison_id`, `results` array (scores per model), `langfuse_url`

### Verification Checklist

- [x] `GET /evals/models` returns registry
- [x] `GET /evals/criteria` returns available criteria
- [x] `POST /evals/compare` runs prompt against models
- [x] `POST /evals/compare` with `save_to_dataset` creates dataset item
- [x] Scores calculated correctly for structure_complete
- [x] Traces visible in Langfuse Cloud (via trace_id)
- [ ] Costs calculated automatically by Langfuse (visible in Langfuse UI, not returned in API yet)
- [x] Partial results returned on model failure
- [x] n8n workflow v02 deployed and activated
- [x] n8n webhook /generate-v2 returns comparison results

---

## Spec Revisions

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-01-13 | Initial implementation - compare endpoint, structure_complete evaluator, Langfuse v2 API integration |
| 0.1.1 | 2026-01-14 | Added n8n workflow v02 with Langfuse integration |

---

## Iteration Path

| Version | Focus |
|---------|-------|
| **v0.1** | Compare endpoint + structure_complete + dataset save |
| v0.2 | LLM-as-judge evals (age_appropriate, engaging) |
| v0.3 | Structured output support |
| v0.4 | Run experiments against full datasets |
