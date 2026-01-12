# Project Instructions for Claude

## Execution Environment

### Backend (Python/LangGraph)

All backend commands run inside the `backend` Docker container:

- **Rebuild:** `docker compose down && docker compose up -d --build`
- **Run tests:** `docker compose exec backend pytest [path/to/test]`
- **Shell access:** `docker compose exec backend /bin/bash`

After rebuilding, always initialize the database:

```bash
docker compose exec backend python init_db.py
```

This creates the DynamoDB tables in the local container. Without this, API requests will fail with 500 errors.

### n8n (Workflow Automation)

n8n workflows are managed via REST API. Workflow JSON files are stored in `n8n/workflows/`.

**IMPORTANT:** Always use the wrapper script for API calls (handles auth automatically):

```bash
./n8n/api.sh <endpoint> [curl-args...]
```

#### API Operations

```bash
# List workflows
./n8n/api.sh workflows

# Get single workflow
./n8n/api.sh workflows/{id}

# Create workflow
./n8n/api.sh workflows -X POST -H "Content-Type: application/json" -d @workflow.json

# Update workflow
./n8n/api.sh workflows/{id} -X PUT -H "Content-Type: application/json" -d @workflow.json

# Activate/Deactivate workflow
./n8n/api.sh workflows/{id}/activate -X POST
./n8n/api.sh workflows/{id}/deactivate -X POST

# Delete workflow
./n8n/api.sh workflows/{id} -X DELETE
```

#### Workflow Iteration Loop

1. Edit JSON in `n8n/workflows/`
2. Update: `./n8n/api.sh workflows/{id} -X PUT -d @n8n/workflows/file.json`
3. Activate: `./n8n/api.sh workflows/{id}/activate -X POST`
4. Test: `curl -X POST http://localhost:5678/webhook/<path> -d '{...}'`
5. Export: `./n8n/api.sh workflows/{id} > n8n/workflows/<file>.json`

#### OpenAI Integration Note

Use `n8n-nodes-base.httpRequest` for OpenAI calls instead of the native OpenAI nodes. The LangChain node doesn't properly pass custom messages. See `backend/specs/007-n8n-lesson-generator/spec.md` for details.

## Architecture Rules

- **Framework:** LangGraph only
- **State:** Single `GraphState` TypedDict in `app/graph/state.py`
- **Routing:** Use Pydantic tools bound to LLM (never `if/elif` on raw user text)
- **Pausing:** Only use `interrupt_after` in graph's `compile()` method
