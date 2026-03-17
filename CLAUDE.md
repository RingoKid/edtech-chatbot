# Project Instructions for Claude

## Architecture Rules

- **Framework:** LangGraph only
- **State:** Single `GraphState` TypedDict in `app/graph/state.py`
- **Routing:** Use Pydantic tools bound to LLM (never `if/elif` on raw user text)
- **Pausing:** Only use `interrupt_after` in graph's `compile()` method

## Development Workflow

Use `/dev` to list all available sub-skills. Key commands:

- `/dev todo` — view and manage project tasks
- `/dev implement` — implement with rebuild-test-fix loop
- `/dev test` — run tests/evals (spawnable as background agent)
- `/dev review` — review diffs or audit test coverage
- `/dev docs` — manage reference materials from Dropbox
- `/dev devops` — AWS status, deploys, health checks

All sub-skills share context from `.claude/commands/dev/_context.md` (Docker commands, paths, script runners).

## Specs

Specs live in `backend/specs/`. Use for new architecture only — iterative work uses `/dev implement` directly from TODO items. See `backend/specs/README.md` for structure and conventions.
