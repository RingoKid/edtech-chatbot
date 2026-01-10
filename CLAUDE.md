# Project Instructions for Claude

## Execution Environment

All commands run inside the `backend` Docker container:

- **Rebuild:** `docker compose down && docker compose up -d --build`
- **Run tests:** `docker compose exec backend pytest [path/to/test]`
- **Shell access:** `docker compose exec backend /bin/bash`

After rebuilding, always initialize the database:

```bash
docker compose exec backend python init_db.py
```

This creates the DynamoDB tables in the local container. Without this, API requests will fail with 500 errors.

## Architecture Rules

- **Framework:** LangGraph only
- **State:** Single `GraphState` TypedDict in `app/graph/state.py`
- **Routing:** Use Pydantic tools bound to LLM (never `if/elif` on raw user text)
- **Pausing:** Only use `interrupt_after` in graph's `compile()` method
