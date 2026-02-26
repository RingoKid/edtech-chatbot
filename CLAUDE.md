# Project Instructions for Claude

## Execution Environment

### Backend (Python/LangGraph)

All backend commands run inside the `backend` Docker container:

- **Rebuild:** `docker compose down && docker compose up -d --build`
- **Run tests:** `docker compose exec backend pytest [path/to/test]`
- **Shell access:** `docker compose exec backend /bin/bash`

### Running Tests and Assessments

**Pytest checks:** Discover with `ls backend/tests/evals/test_*.py`, then ask user which to run.

```bash
docker compose exec backend pytest tests/evals/ -v            # all
docker compose exec backend pytest tests/evals/<file> -v      # specific
```

**LLM judge assessments:** Use `--list` to discover available evals and fixtures. Flags combine freely.

```bash
EVAL_CMD="docker compose exec -e GIT_SHA=$(git rev-parse --short HEAD) backend python scripts/run_scaffolding_evals.py"
$EVAL_CMD --list                                                # discover evals & fixtures
$EVAL_CMD                                                       # run all
$EVAL_CMD --eval verbatim structure --fixture k_letter_t_onlevel  # combine flags
$EVAL_CMD --fixtures-dir tests/fixtures/handwriting_expert      # expert fixtures
```

**Regenerate fixtures** (only if generator code changes):

```bash
docker compose exec -e GIT_SHA=$(git rev-parse --short HEAD) backend python scripts/generate_eval_fixtures.py
```

**After rebuilding**, always init the database (creates local DynamoDB tables, without this API returns 500s):

```bash
docker compose exec backend python scripts/init_db.py
```

## AWS Environment

### Account & Region

- **Account:** 522534289122
- **Region:** us-east-1
- **Domain:** composeearly.com

### Service Identifiers

- **Amplify App ID:** `dyio3npn4doy2` (frontend)
- **App Runner Service:** `edtech-chatbot-service-develop` (backend)
- **ECR Repo:** `522534289122.dkr.ecr.us-east-1.amazonaws.com/edtech-chatbot`
- **DynamoDB Tables:** `EdTechChatbotTable-{env}`, `EdTechChatbotCheckpoints-{env}`

### Quick Status Checks

```bash
# Frontend — last 3 deploys
aws amplify list-jobs --app-id dyio3npn4doy2 --branch-name develop \
  --max-items 3 --query 'jobSummaries[].{Job:jobId,Status:status,Time:endTime,Msg:commitMessage}' \
  --output table

# Backend — service status + last 3 operations
aws apprunner list-services \
  --query 'ServiceSummaryList[?ServiceName==`edtech-chatbot-service-develop`].{Name:ServiceName,Status:Status,URL:ServiceUrl}' \
  --output table

aws apprunner list-operations \
  --service-arn $(aws apprunner list-services --query 'ServiceSummaryList[?ServiceName==`edtech-chatbot-service-develop`].ServiceArn' --output text) \
  --max-results 3 --output table

# Backend health check (live)
curl -s https://mkbifgscip.us-east-1.awsapprunner.com/api/v1/health

# ECR — recent images
aws ecr describe-images --repository-name edtech-chatbot \
  --query 'sort_by(imageDetails,&imagePushedAt)[-3:].{Tags:imageTags,Pushed:imagePushedAt,Size:imageSizeInBytes}' \
  --output table

# DynamoDB — table status
aws dynamodb describe-table --table-name EdTechChatbotTable-sandbox \
  --query 'Table.{Name:TableName,Status:TableStatus,Items:ItemCount}' \
  --output table

# App Runner logs (last 30 min)
aws apprunner list-services --query 'ServiceSummaryList[?ServiceName==`edtech-chatbot-service-develop`].ServiceArn' --output text \
  | xargs -I{} aws logs filter-log-events --log-group-name /aws/apprunner/edtech-chatbot-service-develop \
  --start-time $(date -v-30M +%s000) --limit 50
```

## Architecture Rules

- **Framework:** LangGraph only
- **State:** Single `GraphState` TypedDict in `app/graph/state.py`
- **Routing:** Use Pydantic tools bound to LLM (never `if/elif` on raw user text)
- **Pausing:** Only use `interrupt_after` in graph's `compile()` method

## Spec Best Practices

Specs live in `backend/specs/`. See `backend/specs/README.md` for structure.

### Required Sections (add after implementation)

Every implemented spec should have:

1. **Implementation Status** — Table showing ✅ Done / 🔲 Planned for each component
2. **Implementation Files** — Table linking to actual code files
3. **Verification** — Testable commands (curl, pytest) with expected output
4. **Spec Revisions** — Version history table

### Key Principles

- **Testable > descriptive** — "Run this curl, expect this output" beats "the system should work"
- **Link to code** — Reference actual file paths, not abstract descriptions
- **Keep status in sync** — Update `backend/specs/README.md` when implementation status changes
- **Record decisions** — Use ADRs in `decisions/` folder for significant architectural choices
- **Single source of truth** — Avoid duplicating info across multiple docs
