---
description: Run tests and evals, report results — spawnable as background agent
---

# /dev test

Read the shared context first: `.claude/commands/dev/_context.md`

## Arguments

`$ARGUMENTS` — what to test:

- (empty) → Auto-discover from `git diff`: map changed files to relevant tests
- `"pytest"` → Run all pytest: `docker compose exec backend pytest tests/evals/ -v`
- `"evals"` → Run all LLM judge evals: `python scripts/run_scaffolding_evals.py`
- `"evals --eval verbatim structure"` → Specific eval criteria
- `"fixtures"` → Regenerate fixtures: `python scripts/generate_eval_fixtures.py`
- Test file path → Run that specific test

## Auto-discovery mapping

| Changed file | Tests to run |
|---|---|
| `handwriting_generator.py` | pytest + LLM judge evals. Warn: fixtures may need regeneration. |
| `reference_materials/handwriting/*` | LLM judge evals (verbatim, activity_naming) |
| `tests/evals/rubrics/*` | LLM judge evals for that rubric |
| `state.py`, `graph.py` | Full pytest suite |

## Report format

```
✅ AGENT DONE: test results
- pytest: 12/12 passed
- evals: verbatim 85%, structure 92%, activity_naming 78%
- ⚠️ activity_naming dropped from 90% → 78% (regression?)
```

Flag any score drops as potential regressions.
