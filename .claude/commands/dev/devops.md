---
description: Check AWS status, deployments, logs, and service health
---

# /dev devops

Read the shared context first: `.claude/commands/dev/_context.md`

## Arguments

`$ARGUMENTS` — what to check:

- (empty) → Full status: frontend deploys, backend service, health check
- `"health"` → Just the backend health check
- `"logs"` → App Runner logs (last 30 min)
- `"deploy"` → Latest frontend + backend deploy status
- Free text → Custom check (e.g., `"is the backend healthy after my push?"`)

## AWS Identifiers

- **Region:** us-east-1
- **Amplify App ID:** `dyio3npn4doy2` (frontend)
- **App Runner Service:** `edtech-chatbot-service-develop` (backend)
- **ECR Repo:** `522534289122.dkr.ecr.us-east-1.amazonaws.com/edtech-chatbot`
- **DynamoDB Tables:** `EdTechChatbotTable-{env}`, `EdTechChatbotCheckpoints-{env}`
- **Health URL:** `https://mkbifgscip.us-east-1.awsapprunner.com/api/v1/health`

## Status Commands

```bash
# Frontend — last 3 deploys
aws amplify list-jobs --app-id dyio3npn4doy2 --branch-name develop \
  --max-items 3 --query 'jobSummaries[].{Job:jobId,Status:status,Time:endTime,Msg:commitMessage}' \
  --output table

# Backend — service status
aws apprunner list-services \
  --query 'ServiceSummaryList[?ServiceName==`edtech-chatbot-service-develop`].{Name:ServiceName,Status:Status,URL:ServiceUrl}' \
  --output table

# Backend — last 3 operations
aws apprunner list-operations \
  --service-arn $(aws apprunner list-services --query 'ServiceSummaryList[?ServiceName==`edtech-chatbot-service-develop`].ServiceArn' --output text) \
  --max-results 3 --output table

# Health check
curl -s https://mkbifgscip.us-east-1.awsapprunner.com/api/v1/health

# App Runner logs (last 30 min)
aws apprunner list-services --query 'ServiceSummaryList[?ServiceName==`edtech-chatbot-service-develop`].ServiceArn' --output text \
  | xargs -I{} aws logs filter-log-events --log-group-name /aws/apprunner/edtech-chatbot-service-develop \
  --start-time $(date -v-30M +%s000) --limit 50
```

## Report format

```
✅ AGENT DONE: AWS status
- Frontend: last deploy SUCCESS (2026-03-16 "merge feature/021...")
- Backend: RUNNING, healthy
- ECR: latest image pushed 2026-03-16
```

Use reporting markers per `_context.md`.
