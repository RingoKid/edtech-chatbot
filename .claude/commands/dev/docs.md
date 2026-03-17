---
description: Manage reference materials — check for updates, convert new files, track what's current
---

# /dev docs

**Run mode:** agent-safe (status check, conversions) — review changes via `git diff` before committing.

Read the shared context first: `.claude/commands/dev/_context.md`

## Arguments

`$ARGUMENTS` — what to do:

- (empty) → **Status check**: scan Dropbox and codebase, report what's new/stale/missing
- `"form D was updated"` → Find in Dropbox, convert, write to codebase, report what changed
- `"new file: Activity Framework"` → Find in Dropbox, convert, save to correct destination
- `"convert <path>"` → Direct conversion of a specific .docx file

## Dropbox → Codebase Mapping

Root: `~/Library/CloudStorage/Dropbox/`

| Dropbox Folder | Codebase Destination |
|---|---|
| `Handwriting & Spelling (Transcription) AI Codes/` | `backend/prompt/reference_materials/handwriting/` |
| `Handwriting & Spelling (Transcription) AI Codes/Supplementary Forms/` | `backend/prompt/reference_materials/handwriting/` |
| `Vocabulary & Syntax (language construction) AI codes/` | `backend/prompt/reference_materials/vocabulary_syntax/` |
| `Idea Generation & Organization AI Codes/` | `backend/prompt/reference_materials/idea_generation/` |

Expert feedback / test plans → `backend/resources/expert-feedback/`

## Status Check (no arguments)

1. List `.docx` files in the Dropbox folders above
2. List `.md` files in codebase reference material directories
3. Read `backend/resources/docs-manifest.json` for conversion history
4. Report: `❌ MISSING` / `⚠️ STALE` / `✅ CURRENT` / `ℹ️ LOCAL ONLY`

## Converting a File

1. **Find** the file in Dropbox folders (match by filename keywords)
2. **Extract** using the utility venv:
   ```bash
   backend/scripts/venv/bin/python backend/scripts/extract_docx.py "<path>"
   ```
3. **Format** the JSON output as clean markdown:
   - Use document structure (headings, paragraphs, tables)
   - Insert comments as: `> **[Author] (YYYY-MM-DD):** text`
   - Preserve emoji markers (💡 🗣️ 💬 👉 🤚 ✏️ 🔄)
4. **Save** to the correct codebase destination (use mapping above, follow existing naming: lowercase, hyphens, `.md`)
5. **Update** `backend/resources/docs-manifest.json`:
   ```json
   {
     "<file-key>": {
       "source": "<dropbox-path>",
       "destination": "<codebase-path>",
       "last_converted": "<ISO-8601>",
       "comment_count": <number>
     }
   }
   ```
6. **Report** what was done:
   ```
   ✅ AGENT DONE: converted form-d-scaffolded-activities
   - Source: ~/Library/CloudStorage/Dropbox/.../Form D.docx
   - Saved to: backend/prompt/reference_materials/handwriting/form-d-scaffolded-activities.md
   - 5 comments found (3 from Dr. Farrow)
   - Review changes with: git diff
   ```

## Important

- **Don't ask, just do it.** The user reviews via `git diff` before committing. If something looks wrong, `git restore` undoes it.
- If comments contain actionable feedback, add items to `backend/resources/TODO.md`.
- Use reporting markers per `_context.md`.
