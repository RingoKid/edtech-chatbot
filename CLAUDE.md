# Project Instructions for Claude

## Execution Environment

### Backend (Python/LangGraph)

All backend commands run inside the `backend` Docker container:

- **Rebuild:** `docker compose down && docker compose up -d --build`
- **Run tests:** `docker compose exec backend pytest [path/to/test]`
- **Shell access:** `docker compose exec backend /bin/bash`

### Running Tests and Assessments

**Pytest-based checks** (routing, params, structure):

1. **Discover** — List all test files: `ls backend/tests/evals/test_*.py`
2. **Present** — Show the available tests to the user
3. **Ask** — Which test(s) to run? (or "all")
4. **Run** — `docker compose exec backend pytest tests/evals/<selected_file> -v`

To run all pytest checks at once: `docker compose exec backend pytest tests/evals/ -v`

**LLM judge assessments** (scaffolding, instructional quality, formatting):

Discover available assessments and fixtures:

```bash
docker compose exec backend python scripts/run_scaffolding_evals.py --list
```

Run assessments:

```bash
# All assessments on all generated fixtures
docker compose exec -e GIT_SHA=$(git rev-parse --short HEAD) backend python scripts/run_scaffolding_evals.py

# Specific assessment(s) only (use --list to see valid names)
docker compose exec -e GIT_SHA=$(git rev-parse --short HEAD) backend python scripts/run_scaffolding_evals.py --eval verbatim structure

# Specific fixture only
docker compose exec -e GIT_SHA=$(git rev-parse --short HEAD) backend python scripts/run_scaffolding_evals.py --fixture k_letter_t_onlevel

# Run against expert fixtures (human-authored ground truth)
docker compose exec -e GIT_SHA=$(git rev-parse --short HEAD) backend python scripts/run_scaffolding_evals.py --fixtures-dir tests/fixtures/handwriting_expert

# Combine flags freely
docker compose exec -e GIT_SHA=$(git rev-parse --short HEAD) backend python scripts/run_scaffolding_evals.py --eval grade_standards --fixtures-dir tests/fixtures/handwriting_expert
```

**Regenerate fixtures** (only needed if generator code changes):

```bash
docker compose exec -e GIT_SHA=$(git rev-parse --short HEAD) backend python scripts/generate_eval_fixtures.py
```

The `-e GIT_SHA=...` flag embeds the current commit hash in reports/fixtures for provenance tracking.

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
