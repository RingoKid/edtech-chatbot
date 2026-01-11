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

**API Base:** `http://localhost:5678/api/v1`
**Auth Header:** `X-N8N-API-KEY: <key>` (get from n8n UI → Settings → API)

#### API Operations

```bash
# List workflows
curl -s http://localhost:5678/api/v1/workflows -H "X-N8N-API-KEY: $N8N_API_KEY"

# Export (get workflow JSON)
curl -s http://localhost:5678/api/v1/workflows/{id} -H "X-N8N-API-KEY: $N8N_API_KEY" > workflow.json

# Import (create new workflow)
curl -s -X POST http://localhost:5678/api/v1/workflows \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d @workflow.json

# Update workflow (requires: name, nodes, connections, settings)
curl -s -X PUT http://localhost:5678/api/v1/workflows/{id} \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"name": "...", "nodes": [...], "connections": {...}, "settings": {}}'

# Activate workflow
curl -s -X POST http://localhost:5678/api/v1/workflows/{id}/activate \
  -H "X-N8N-API-KEY: $N8N_API_KEY"

# Deactivate workflow
curl -s -X POST http://localhost:5678/api/v1/workflows/{id}/deactivate \
  -H "X-N8N-API-KEY: $N8N_API_KEY"

# Delete workflow
curl -s -X DELETE http://localhost:5678/api/v1/workflows/{id} \
  -H "X-N8N-API-KEY: $N8N_API_KEY"
```

#### Workflow Iteration Loop

1. Edit JSON in `n8n/workflows/`
2. Update: `curl -X PUT .../workflows/{id}` with workflow JSON
3. Activate: `curl -X POST .../workflows/{id}/activate`
4. Test: `curl -X POST http://localhost:5678/webhook/<path> -d '{...}'`
5. Export: `curl -s .../workflows/{id} > n8n/workflows/<file>.json`

#### OpenAI Integration Note

Use `n8n-nodes-base.httpRequest` for OpenAI calls instead of the native OpenAI nodes. The LangChain node doesn't properly pass custom messages. See `backend/specs/007-n8n-lesson-generator/spec.md` for details.

## Architecture Rules

- **Framework:** LangGraph only
- **State:** Single `GraphState` TypedDict in `app/graph/state.py`
- **Routing:** Use Pydantic tools bound to LLM (never `if/elif` on raw user text)
- **Pausing:** Only use `interrupt_after` in graph's `compile()` method
