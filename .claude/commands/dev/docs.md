---
description: Manage reference materials — check for updates, convert new files, track what's current
---

# /dev docs

Read the shared context first: `.claude/commands/dev/_context.md`

## Arguments

`$ARGUMENTS` — what to do. Examples:

- (empty) → **Status check**: scan Dropbox and codebase, report what's new/stale/missing
- `"form D was updated"` → Find the file in Dropbox, convert, show diff against codebase version, ask before replacing
- `"new file: Activity Framework"` → Find in Dropbox, convert, ask where to save
- `"convert <path>"` → Direct conversion of a specific file (delegates to `/dev convert`)

## Dropbox Location

Root: `~/Library/CloudStorage/Dropbox/`

Reference materials are organized by language process:

| Dropbox Folder | Codebase Destination |
|---|---|
| `Handwriting & Spelling (Transcription) AI Codes/` | `backend/prompt/reference_materials/handwriting/` |
| `Handwriting & Spelling (Transcription) AI Codes/Supplementary Forms/` | `backend/prompt/reference_materials/handwriting/` |
| `Vocabulary & Syntax (language construction) AI codes/` | `backend/prompt/reference_materials/vocabulary_syntax/` |
| `Idea Generation & Organization AI Codes/` | `backend/prompt/reference_materials/idea_generation/` |

Expert feedback and test plans go to: `backend/resources/expert-feedback/`

## Status Check (no arguments)

1. List all `.docx` files in the Dropbox folders above (with modification dates)
2. List all `.md` files in the codebase reference material directories
3. Read `backend/resources/docs-manifest.json` for conversion history
4. Report:
   - Files in Dropbox with no codebase equivalent → `❌ MISSING`
   - Files converted but Dropbox version is newer than last conversion → `⚠️ STALE`
   - Files up to date → `✅ CURRENT`
   - Files in codebase with no Dropbox source → `ℹ️ LOCAL ONLY`

## Converting a File

When the user says a file was updated or asks to add a new file:

1. **Find the file** in the Dropbox folders. Match by filename keywords (fuzzy is fine).
2. **Extract** using the utility venv:
   ```bash
   backend/scripts/venv/bin/python backend/scripts/extract_docx.py "<dropbox-path>"
   ```
3. **Check for comments** — if `comment_count > 0`, highlight this to the user. Comments often contain actionable feedback.
4. **If updating an existing file**: diff the new extraction against the current codebase version. Show what changed (new activities, removed content, etc.) before overwriting.
5. **If adding a new file**: suggest a destination path following existing naming conventions (lowercase, hyphens, `.md`). Ask the user before saving.
6. **After saving**: update `backend/resources/docs-manifest.json`:
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
7. **If comments contained feedback**: ask the user if TODO.md should be updated.

## Important

- **Never auto-replace codebase files** — always show the diff and ask first. Reference material changes can alter generator behavior.
- Use `⚠️ AGENT ERROR:`, `ℹ️ AGENT NOTE:`, `✅ AGENT DONE:` markers per `_context.md`.
- The extraction script runs locally (not in Docker): `backend/scripts/venv/bin/python`
