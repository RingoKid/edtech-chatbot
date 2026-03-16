---
description: Convert a .docx file to markdown, preserving comments with author and date
---

# /dev convert

Read the shared context first: `.claude/commands/dev/_context.md`

## Arguments

`$ARGUMENTS` — path to a `.docx` file (absolute or relative to project root)

## What This Does

Converts a `.docx` file to structured markdown, preserving:
- Full document body text (paragraphs, tables)
- Inline comments with author, date, and anchored paragraph context

## Steps

### 1. Validate Input

- Check that the file exists and is a `.docx` file
- If the path looks like a Dropbox URL or relative Dropbox path, resolve it to the local filesystem. Check common Dropbox locations: `~/Library/CloudStorage/Dropbox/`, `~/Dropbox/`

### 2. Extract

Run the extraction script:

```bash
python3 backend/scripts/extract_docx.py "$ARGUMENTS"
```

This outputs JSON with `paragraphs` (each with `text` and `comments` array) and `tables`.

### 3. Agent Formats Markdown

Take the JSON output and produce clean markdown:

- Use document structure (headings, paragraphs, tables) from the body text
- Insert comments as blockquotes directly below their anchored paragraph:
  ```
  > **[Author Name] (YYYY-MM-DD):** comment text
  ```
- If the document has tables, format them as markdown tables
- Preserve emoji markers (💡 🗣️ 💬 👉 🤚 ✏️ 🔄) — these are part of the lesson plan format

### 4. Output

- Print the full markdown to the chat
- Ask the user where to save it (suggest `backend/resources/expert-feedback/<descriptive-name>.md`)
- If a file already exists at that location, show a diff of what changed (new comments, modified text) before overwriting

### 5. Update Tracking

- If saved, update `backend/resources/docs-manifest.json` with:
  ```json
  {
    "<file-key>": {
      "source": "<original-docx-path>",
      "destination": "<saved-markdown-path>",
      "last_converted": "<ISO-8601 timestamp>",
      "comment_count": <number>
    }
  }
  ```
- If `TODO.md` should be updated (e.g., new comments = new action items), note this to the user but don't auto-add — let `/dev docs` or the user handle that

## Error Handling

If `extract_docx.py` fails or produces empty output, report:
```
⚠️ AGENT ERROR: Failed to extract <filename> — <reason>
```
