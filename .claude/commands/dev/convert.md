---
description: Convert a .docx file to markdown, preserving comments with author and date
---

# /dev convert

**Run mode:** agent-safe — saves output, review via `git diff` before committing.

Read the shared context first: `.claude/commands/dev/_context.md`

## Arguments

`$ARGUMENTS` — path to a `.docx` file (absolute or relative to project root)

## Steps

1. **Validate** — check file exists and is `.docx`. Resolve Dropbox URLs/paths to local filesystem.
2. **Extract** using the utility venv:
   ```bash
   backend/scripts/venv/bin/python backend/scripts/extract_docx.py "$ARGUMENTS"
   ```
3. **Format** the JSON output as clean markdown:
   - Use document structure (headings, paragraphs, tables)
   - Insert comments as: `> **[Author] (YYYY-MM-DD):** text`
   - Preserve emoji markers (💡 🗣️ 💬 👉 🤚 ✏️ 🔄)
4. **Save** to `backend/resources/expert-feedback/<descriptive-name>.md`
5. **Update** `backend/resources/docs-manifest.json` with source, destination, timestamp, comment count
6. **Report:**
   ```
   ✅ AGENT DONE: converted <filename>
   - Saved to: <path>
   - Comments: <count>
   - Review changes with: git diff
   ```

## Error Handling

```
⚠️ AGENT ERROR: Failed to extract <filename> — <reason>
```
