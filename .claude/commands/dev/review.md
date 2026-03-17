---
description: Review code diff or audit test coverage against a plan
---

# /dev review

**Run mode:** agent-safe for `"diff"` mode. For `"plan"` mode, pass the plan as an argument or file path — agents can't access main chat context.

Read the shared context first: `.claude/commands/dev/_context.md`

## Arguments

`$ARGUMENTS` — what to review:

- (empty) → Review uncommitted changes against the TODO item being worked on
- `"plan"` → Audit the current plan: will existing tests/evals catch all the changes?
- `"diff"` → Review `git diff` for quality, regressions, missed spots
- Free text → Custom review focus (e.g., `"check if prompt rules still match Form D"`)

## Review mode (default / "diff")

1. Read `git diff` (staged + unstaged)
2. Identify which TODO item(s) the changes address
3. Check:
   - Does the diff actually fix what the TODO describes?
   - Any obvious regressions? (removed code that was needed, contradicting prompt rules)
   - Any reference material dependencies broken?
4. Report: approve / concerns / blockers

## Audit mode ("plan")

1. Read the current plan (from plan mode or provided description)
2. Read existing tests in `tests/evals/` and rubrics in `tests/evals/rubrics/`
3. For each planned change, check:
   - Is there a test/eval that would catch a regression?
   - Are there gaps? (change has no coverage)
4. Report:
   - Covered changes
   - **Gaps**: changes with no test coverage + suggestions for what to add

## Rules

- Be specific: "line 74 of handwriting_generator.py still references LOW-LEVEL tags that Form D no longer has" — not vague concerns.
- Use reporting markers per `_context.md`.
