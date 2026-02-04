# Project Instructions for Claude

## Execution Environment

### Backend (Python/LangGraph)

All backend commands run inside the `backend` Docker container:

- **Rebuild:** `docker compose down && docker compose up -d --build`
- **Run tests:** `docker compose exec backend pytest [path/to/test]`
- **Shell access:** `docker compose exec backend /bin/bash`

### Evals

When asked to run evals:

1. **Discover** — List all eval files: `ls backend/tests/evals/test_*.py`
2. **Present** — Show the available evals to the user
3. **Ask** — Which eval(s) to run? (or "all")
4. **Run** — `docker compose exec backend pytest tests/evals/<selected_file> -v`

To run all evals at once: `docker compose exec backend pytest tests/evals/ -v`

After rebuilding, always initialize the database:

```bash
docker compose exec backend python scripts/init_db.py
```

This creates the DynamoDB tables in the local container. Without this, API requests will fail with 500 errors.

## Architecture Rules

- **Framework:** LangGraph only
- **State:** Single `GraphState` TypedDict in `app/graph/state.py`
- **Routing:** Use Pydantic tools bound to LLM (never `if/elif` on raw user text)
- **Pausing:** Only use `interrupt_after` in graph's `compile()` method

## Spec Best Practices

Specs live in `backend/specs/`. See `backend/specs/README.md` for structure.

### Required Sections (add after implementation)

Every implemented spec should have:

1. **Implementation Status** — Table showing ✅ Done / 🔲 Planned for each component
2. **Implementation Files** — Table linking to actual code files
3. **Verification** — Testable commands (curl, pytest) with expected output
4. **Spec Revisions** — Version history table

### Key Principles

- **Testable > descriptive** — "Run this curl, expect this output" beats "the system should work"
- **Link to code** — Reference actual file paths, not abstract descriptions
- **Keep status in sync** — Update `backend/specs/README.md` when implementation status changes
- **Record decisions** — Use ADRs in `decisions/` folder for significant architectural choices
- **Single source of truth** — Avoid duplicating info across multiple docs
