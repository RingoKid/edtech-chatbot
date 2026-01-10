---
description: Implement a feature from spec with rebuild-test-fix workflow
---

You are implementing a feature following the mandatory development workflow.

## Arguments

- `$ARGUMENTS` - Path to the spec file (e.g., `backend/specs/007-new-feature/spec.md`)

## Workflow Steps

Follow these steps **in order**. Do not skip steps.

### 1. Read the Spec

First, read the spec file at `$ARGUMENTS` to understand what needs to be implemented.

Also read `backend/specs/000-project-common.md` for architectural rules if you haven't already.

### 2. Implement

Write the code according to the spec. Follow the architecture rules:

- Use LangGraph for all agent logic
- Use single `GraphState` TypedDict in `app/graph/state.py`
- Use Pydantic tools for routing (never `if/elif` on raw text)
- Only use `interrupt_after` in graph's `compile()` for pausing

### 3. Rebuild (MANDATORY)

After writing code, **you MUST rebuild** the container:

```bash
docker compose down && docker compose up -d --build
```

Then initialize the database:

```bash
docker compose exec backend python init_db.py
```

### 4. Test

Run the tests specified in the spec:

```bash
docker compose exec backend pytest [path/to/test_file.py] -v
```

### 5. Fix & Iterate

If tests fail:
1. Debug and fix the code
2. **Return to Step 3 (Rebuild)** - this is mandatory after every code change
3. Test again
4. Repeat until all tests pass

### 6. Spec Sync (MANDATORY FINAL STEP)

Once all tests pass, you **MUST** propose changes to sync the spec file with the final working code.

Tell the user:
> "All tests pass. I'll now propose spec-sync changes to update `[spec file]` to match the final implementation."

Then:
- Identify any discrepancies between the spec and actual code
- Propose specific edits to the spec file
- Wait for user approval before making changes

## Checklist

Use this checklist to track progress:

- [ ] Read and understand the spec
- [ ] Implement the feature
- [ ] Rebuild container
- [ ] Initialize database
- [ ] Run tests
- [ ] All tests passing
- [ ] Propose spec-sync changes
- [ ] Spec updated (after user approval)

## Important Reminders

- **Never skip the rebuild step** - code changes won't take effect without it
- **Always run tests inside Docker** - never run pytest directly on host
- **Spec sync is mandatory** - the spec must reflect the final implementation
