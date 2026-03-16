# Shared Context for /dev Sub-skills

## Project Structure

| Area | Path |
|------|------|
| Reference materials | `backend/prompt/reference_materials/handwriting/` |
| Expert feedback | `backend/resources/expert-feedback/` |
| Evals (tests, rubrics, fixtures) | `backend/tests/evals/` |
| Eval rubrics | `backend/tests/evals/rubrics/` |
| Eval fixtures | `backend/tests/fixtures/` |
| Eval results | `backend/tests/evals/results/` |
| Scripts | `backend/scripts/` |
| Specs | `backend/specs/` |
| Docs manifest | `backend/resources/docs-manifest.json` |
| Project TODO | `backend/resources/TODO.md` |

## Dropbox

Local sync path: `~/Library/CloudStorage/Dropbox/`

| Folder | Contents |
|--------|----------|
| `Handwriting & Spelling (Transcription) AI Codes/` | Main transcription forms + training codes |
| `Handwriting & Spelling (Transcription) AI Codes/Supplementary Forms/` | Forms A, D, F, H + PDFs (E, G, standards) |
| `Vocabulary & Syntax (language construction) AI codes/` | Vocab/syntax forms |
| `Idea Generation & Organization AI Codes/` | Idea gen forms |

To resolve a Dropbox URL to a local path, strip the URL and match the filename to the local sync folder.

## Running Scripts

Two runners depending on what the script needs:

| Type | Runner | When |
|------|--------|------|
| **Utility** (filesystem access, Dropbox, conversion) | `backend/scripts/venv/bin/python backend/scripts/<script>.py` | Needs local files |
| **App** (evals, fixtures, DB, anything with app deps) | `docker compose exec backend python scripts/<script>.py` | Needs LangChain, LangGraph, etc. |

Utility venv: `backend/scripts/venv/` (gitignored). Dependencies: `backend/scripts/requirements-utils.txt`.

### Docker Commands

- **Rebuild:** `docker compose down && docker compose up -d --build`
- **Init DB:** `docker compose exec backend python scripts/init_db.py`
- **Run tests:** `docker compose exec backend pytest <path> -v`
- **Run evals:** `docker compose exec -e GIT_SHA=$(git rev-parse --short HEAD) backend python scripts/run_scaffolding_evals.py`

## Agent Reporting

When a sub-skill spawns agents, agents must report back to the main chat using these markers:

- `⚠️ AGENT ERROR:` — something broke, needs user attention
- `ℹ️ AGENT NOTE:` — informational, user should be aware
- `✅ AGENT DONE:` — task completed successfully with summary

Never silently fail. If an agent hits an issue it can't resolve, report it and stop.

## TODO Tracking

- Project TODO lives at: `backend/resources/TODO.md`
- After completing work, update `TODO.md` if any items were resolved or new ones discovered
- Format: grouped by source, checkbox style `- [ ]` / `- [x]`
- Include the date and source when adding new items
