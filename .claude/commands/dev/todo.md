---
description: View, add, or check off project TODO items
---

# /dev todo

Read the shared context first: `.claude/commands/dev/_context.md`

TODO file: `backend/resources/TODO.md`

## Arguments

`$ARGUMENTS` — what to do:

- (empty) → Show the TODO with per-section progress counts
- `"add <text>"` → Add item to the right section (format: `- [ ] **Title** — detail (source, date)`)
- `"done <keyword>"` → Mark matching item `[x]`. If ambiguous, ask.
- free text → Treat as instructions (e.g., "move Form D to the top")

## Rules

- Never silently rewrite or reorder — show what changed
- Convert relative dates to absolute when adding items
- Use reporting markers per `_context.md`
