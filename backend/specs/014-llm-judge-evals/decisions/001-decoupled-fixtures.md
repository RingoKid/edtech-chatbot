# ADR-001: Decoupled Fixture Generation from Eval Runs

## Status
Accepted

## Context
LLM judge evals need lesson plan outputs to evaluate. We had two options:
1. Generate lessons live during each eval run (like the existing rule-based evals in `test_handwriting_generator.py`)
2. Pre-generate lessons as JSON fixtures, then run judges against saved outputs

The existing rule-based evals run the full graph for every test, which takes ~5 minutes per test case (routing → params → generation). Running 15 judge evals on live outputs would take 75+ minutes per eval run.

## Decision
Decouple generation from evaluation. Generate fixtures once via `scripts/generate_eval_fixtures.py`, save as JSON, and run judges against saved outputs.

## Consequences
**Benefits:**
- Eval runs are fast (~2.5 min for 15 tests) — only judge LLM calls, no graph execution
- Deterministic eval inputs — same lesson is judged every time, reducing noise
- One fixture set serves multiple eval criteria (level_appropriate, within_activity, etc.)
- Cheaper — fixture generation is a one-time cost, not per-eval-run

**Trade-offs:**
- Fixtures can become stale if the generator prompt changes (must re-run `generate_eval_fixtures.py`)
- Fixtures skip existing (use `--force` to regenerate all)
- Two-step process for first-time setup (generate fixtures, then run evals)
