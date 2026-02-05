---
description: Implement a feature from spec with rebuild-test-fix workflow
---

You are implementing a feature following the mandatory development workflow.

## Arguments

- `$ARGUMENTS` - Path to the spec file (e.g., `backend/specs/007-new-feature/spec.md` or `frontend/specs/001-feature/spec.md`)

## Detect Context

**Check the spec path to determine context:**

- If path starts with `backend/` → **Backend context**
- If path starts with `frontend/` → **Frontend context**

## Workflow Steps

Follow these steps **in order**. Do not skip steps.

### 1. Read the Spec

First, read the spec file at `$ARGUMENTS` to understand what needs to be implemented.

**Backend only:** Also read `backend/specs/000-project-common.md` for architectural rules.

### 2. Look Up Latest Docs (Context7)

Before writing code, use **Context7 MCP tools** to pull up-to-date documentation for any libraries/frameworks referenced in the spec:

1. Scan the spec for libraries (e.g., LangChain, LangGraph, Pydantic, React, etc.)
2. Call `resolve-library-id` for each library
3. Call `query-docs` with queries specific to what you need to implement

This ensures you use current APIs, not outdated patterns from training data.

### 3. Implement

Write the code according to the spec.

**Backend architecture rules:**
- Use LangGraph for all agent logic
- Use single `GraphState` TypedDict in `app/graph/state.py`
- Use Pydantic tools for routing (never `if/elif` on raw text)
- Only use `interrupt_after` in graph's `compile()` for pausing

**Frontend architecture rules:**
- Use React with Vite
- Follow existing component patterns in the codebase
- Use Tailwind CSS for styling
- Use React Router for navigation

### 4. Rebuild (MANDATORY)

After writing code, **you MUST rebuild** the containers:

```bash
docker compose down && docker compose up -d --build
```

**Backend only** - Initialize the database:

```bash
docker compose exec backend python scripts/init_db.py
```

### 5. Verify

Run the verification commands specified in the spec. Check the spec's **Verification** section for the exact commands.

**Common patterns:**

- **pytest:** `docker compose exec backend pytest [path/to/test_file.py] -v`
- **Eval scripts:** `docker compose exec backend python scripts/[eval_script].py`
- **Frontend tests:** `docker compose exec frontend npm run test`
- **curl checks:** Run the curl commands listed in the spec

Use whatever the spec says — not every feature uses pytest.

### 6. Fix & Iterate

If verification fails:
1. Debug and fix the code
2. **Return to Step 4 (Rebuild)** - this is mandatory after every code change
3. Verify again
4. Repeat until all checks pass

### 7. Spec Sync (MANDATORY FINAL STEP)

Once all verification passes, you **MUST** sync the spec and related docs with the final working code.

Tell the user:
> "All checks pass. I'll now sync the spec and docs with the final implementation."

#### 7.1 Update the Spec File

Ensure the spec includes these sections (add if missing):

**Implementation Status table:**
```markdown
## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Feature X | ✅ Done | `path/to/file.py` |
| Feature Y | 🔲 Planned | Next iteration |
```

**Implementation Files section:**
```markdown
## Implementation Files

| File | Purpose |
|------|---------|
| `app/feature/main.py` | Core logic |
| `tests/test_feature.py` | Unit tests |
```

**Verification section (testable acceptance criteria):**
```markdown
## Verification

### Manual Test
```bash
curl -X POST http://localhost:8000/api/endpoint -d '{"key": "value"}'
```

### Expected Output
- [ ] Returns 200 with `{"success": true}`
- [ ] Database record created
```

**Spec Revisions section:**
```markdown
## Spec Revisions

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | YYYY-MM-DD | Initial implementation |
```

#### 7.2 Update the Specs Index

Update the appropriate specs README:
- **Backend:** `backend/specs/README.md`
- **Frontend:** `frontend/specs/README.md` (create if doesn't exist)

Changes:
- Set correct status (Draft → Implemented)
- Add any new related files
- Link to reviews/incidents if applicable

#### 7.3 Record Key Decisions (if any)

If you made significant architectural decisions during implementation, create an ADR:

```markdown
# ADR-001: Decision Title

## Status
Accepted

## Context
What problem were we solving?

## Decision
What did we decide to do?

## Consequences
What are the trade-offs?
```

Save to: `[backend|frontend]/specs/XXX-feature/decisions/001-decision-name.md`

## Checklist

Use this checklist to track progress:

- [ ] Read and understand the spec
- [ ] Look up latest docs via Context7
- [ ] Implement the feature
- [ ] Rebuild container
- [ ] Initialize database
- [ ] Run verification (pytest, eval scripts, curl, etc.)
- [ ] All checks passing
- [ ] Spec has Implementation Status table
- [ ] Spec has Implementation Files section
- [ ] Spec has Verification section with test commands
- [ ] Spec has Revisions section
- [ ] README.md status updated
- [ ] ADRs created for key decisions (if any)

## Important Reminders

- **Never skip the rebuild step** - code changes won't take effect without it
- **Always run verification inside Docker** - never run pytest or scripts directly on host
- **Spec sync is mandatory** - the spec must reflect the final implementation
- **Specs are for future you** - write them like you'll forget everything in 6 months
- **Testable > descriptive** - "run this curl, expect this output" beats "the system should work"
