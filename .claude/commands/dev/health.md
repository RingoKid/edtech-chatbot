---
description: Quick health check — backend, frontend, OpenAI key, and AWS services
---

# /dev health

**Run mode:** inline (no agent needed). Run all checks directly and report.

Read the shared context first: `.claude/commands/dev/_context.md`

## What to check

Run all of these in parallel where possible:

### 1. Backend API
```bash
curl -s -o /dev/null -w "%{http_code}" https://mkbifgscip.us-east-1.awsapprunner.com/api/v1/health
```
- 200 → OK
- Anything else → report the status code

### 2. Frontend
```bash
curl -s -o /dev/null -w "%{http_code}" https://composeearly.com
```
- 200 → OK
- Anything else → report the status code

### 3. OpenAI API key
```bash
# Reads key from backend/.env — just validates auth, doesn't burn tokens
source backend/.env && curl -s -w "\n%{http_code}" https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY" | tail -1
```
- 200 → Key valid
- 401 → Key revoked or invalid
- 429 → Rate limited or quota exceeded (possible billing issue)

### 4. App Runner status
```bash
aws apprunner list-services \
  --query 'ServiceSummaryList[?ServiceName==`edtech-chatbot-service-develop`].Status' \
  --output text --region us-east-1
```
- RUNNING → OK
- Anything else → report

### 5. DynamoDB
```bash
aws dynamodb describe-table --table-name EdTechChatbotTable-sandbox \
  --query 'Table.TableStatus' --output text --region us-east-1
```
- ACTIVE → OK
- Anything else → report

## Output format

```
Backend:    ✅ 200
Frontend:   ✅ 200
OpenAI key: ✅ valid
App Runner: ✅ RUNNING
DynamoDB:   ✅ ACTIVE
```

If anything fails, use the warning marker:

```
Backend:    ⚠️ 503 — service may be deploying
Frontend:   ✅ 200
OpenAI key: ⚠️ 401 — key revoked or invalid
App Runner: ⚠️ OPERATION_IN_PROGRESS — deployment underway
DynamoDB:   ✅ ACTIVE
```

Keep it tight — no extra commentary unless something is wrong.
