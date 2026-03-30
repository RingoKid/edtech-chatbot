---
description: Run tests and evals, report results — spawnable as background agent
---

# /dev test

**Run mode:** agent-safe — spawnable as background agent for parallel test runs.

Read the shared context first: `.claude/commands/dev/_context.md`

## Arguments

`$ARGUMENTS` — what to test.

## Behavior

### Step 1: Discover

Discover all available tests dynamically — never hardcode paths or filenames:

- List `backend/tests/unit/` for unit tests
- List `backend/tests/integration/` for integration tests
- List `backend/tests/evals/` for LLM judge eval tests
- List `backend/tests/evals/rubrics/` for eval rubric files
- Check if `backend/scripts/run_scaffolding_evals.py` exists for full eval runner
- Check if `backend/scripts/generate_eval_fixtures.py` exists for fixture regeneration

### Step 2: Match

Match `$ARGUMENTS` to discovered tests:

| Argument | Action |
|---|---|
| (empty) | Show summary of all discovered tests grouped by type. Ask what to run. |
| `"unit"` | List all unit test files. Ask which to run (all or specific). |
| `"integration"` | List all integration test files. Ask which to run. |
| `"evals"` | List all eval test files. Ask which to run. |
| `"fixtures"` | Regenerate eval fixtures via script. Confirm first. |
| `"all"` | Run everything. Confirm first. |
| keyword (e.g. `"async"`, `"routing"`) | Search all test filenames for matches across unit/integration/evals. Show matches, ask which to run. |
| file path | Run that specific test file directly. |

**Always ask before running.** Show what you found and what you'll execute. Wait for confirmation.

### Step 3: Run

Run tests using Docker (see `_context.md` for commands):

- **Unit/integration/eval pytest:** `docker compose exec backend pytest <path> -v`
- **Full LLM judge evals:** `docker compose exec -e GIT_SHA=$(git rev-parse --short HEAD) backend python scripts/run_scaffolding_evals.py`
- **Fixtures:** `docker compose exec backend python scripts/generate_eval_fixtures.py`

### Step 4: Report

```
✅ AGENT DONE: test results
- <type>: X/Y passed
- ⚠️ <any failures or regressions>
```

Flag any score drops in evals as potential regressions.
