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

## Worktrees (parallel feature dev)

When a feature is disruptive enough that branch-switching is painful, create a git worktree so two branches stay live side by side.

**Create** (branch from `develop` so the new feature isn't entangled with other branches):
```bash
git fetch origin
git worktree add ../edtech-chatbot-<feature> develop -b <branch-name>
```

**Make it runnable in parallel with the main worktree** — pick a port offset (e.g., `+10` → backend 8010, frontend 3010, dynamodb-local 8011; verify with `lsof -i :8010`):

1. Copy envs: `cp backend/.env{,.local} ../edtech-chatbot-<feature>/backend/`
2. Override host ports in the new worktree's `docker-compose.override.yml`:
   ```yaml
   services:
     backend:
       ports: ["8010:8000"]
     frontend:
       ports: ["3010:5173"]
     dynamodb-local:
       user: root
       ports: ["8011:8000"]
       volumes:
         - dynamodb_data:/home/dynamodblocal/data
       command: ["-jar","DynamoDBLocal.jar","-dbPath","./data","-sharedDb"]
   volumes:
     dynamodb_data:
   ```
3. Hide the override edit from git so local ports don't leak into commits:
   `git update-index --skip-worktree docker-compose.override.yml`
4. Point the frontend at its own backend — create `frontend/.env.local`:
   ```
   VITE_API_BASE_URL=http://localhost:8010/api/v1
   VITE_WS_BASE_URL=ws://localhost:8010
   ```
5. Allow the new frontend origin in backend CORS — append to `backend/.env.local`:
   `FRONTEND_URL=http://localhost:3010`
6. Spin up + seed:
   ```bash
   docker compose up -d --build
   docker compose exec backend python scripts/init_db.py
   ```

**Open in a second VS Code window:** `code -n ~/Projects/edtech-chatbot-<feature>`

**Teardown:**
```bash
git worktree remove ~/Projects/edtech-chatbot-<feature>   # refuses if dirty
git branch -d <branch-name>                                # only if merged to develop
```

**Gotchas:**
- Compose volumes are project-scoped — the new worktree starts with an empty DynamoDB; re-seed if fixtures matter.
- To edit the overridden compose file intentionally later: `git update-index --no-skip-worktree <file>`, commit, re-enable.
- `.env.local` precedence: later assignments win — put overrides (like `FRONTEND_URL`) at the bottom, not the top.

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
