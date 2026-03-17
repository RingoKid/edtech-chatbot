---
description: Implement a TODO item or feature with rebuild-test-fix loop
---

# /dev implement

Read the shared context first: `.claude/commands/dev/_context.md`

## Arguments

`$ARGUMENTS` — what to implement. Accepts:

- TODO keyword (e.g., `"Review section incorrect"`) → looks up in `backend/resources/TODO.md`
- Spec file path (e.g., `"specs/022-split-reference-materials/spec.md"`)
- Free text description (e.g., `"add boxed corrective feedback section"`)

Optionally append test criteria: `"Review section incorrect" --eval verbatim structure`

## Cycle

1. **Understand** — Read the TODO item / spec / description. Read all relevant source files.
2. **Plan** — Enter plan mode. Keep it brief: what files change, what order, what tests verify it. Exit plan mode.
3. **Implement** — Make the changes.
4. **Rebuild** — `docker compose down && docker compose up -d --build && docker compose exec backend python scripts/init_db.py`
5. **Test** — Run specified tests/evals. If none specified, discover from changed files:
   - `handwriting_generator.py` → `pytest tests/evals/test_handwriting_generator.py -v`
   - Generator output changes → `python scripts/run_scaffolding_evals.py`
   - If fixtures are stale, regenerate: `python scripts/generate_eval_fixtures.py`
6. **Fix** — If tests fail, read the failure, fix, go to step 4.
7. **Regression check** — Run full test suite once green.
8. **Report** — Show what changed, test results, update TODO.md (`[x]` completed items).

## Rules

- Never skip the test step. If no tests exist for the change, flag it.
- If a change touches generator prompt rules, check that reference materials support the new rules.
- Batch related TODO items when they share the same code path.
- Use reporting markers per `_context.md`.
