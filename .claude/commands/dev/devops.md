---
description: Check AWS status, deployments, logs, and service health
---

# /dev devops

Spawn a **background agent** with the objective from `$ARGUMENTS` and the context below. For quick one-off checks, run inline instead.

## Arguments

`$ARGUMENTS` — what to check:

- (empty) → Full status: both pipelines + health check
- `"health"` → Just the health endpoint
- `"logs"` → App Runner logs (last 30 min)
- `"deploy"` → Latest frontend + backend deploy status
- `"monitor"` → Poll until current deployment completes (background, max 10 checks, 60s apart)
- Free text → Custom objective

## Deployment Pipelines

Push to `develop` triggers two independent pipelines:

**Frontend (Amplify):**
```
GitHub push → Amplify webhook → npm ci + build → CloudFront CDN
```
- Stages: PROVISIONING → BUILD → DEPLOY → VERIFY → SUCCEED/FAILED
- Typically takes ~2 min

**Backend (CodeBuild → ECR → App Runner):**
```
GitHub push → CodeBuild (buildspec.yml) → Docker build → ECR push (:latest) → App Runner auto-deploy
```
- CodeBuild: builds Docker image, tags with `latest` + commit SHA, pushes to ECR
- App Runner: detects new `latest` image, auto-deploys
- Typically takes ~5 min total

## AWS Identifiers

- **Region:** us-east-1
- **Amplify App ID:** `dyio3npn4doy2` (branch: develop)
- **App Runner Service:** `edtech-chatbot-service-develop`
- **App Runner ARN:** `arn:aws:apprunner:us-east-1:522534289122:service/edtech-chatbot-service-develop/1b0e5f1b973c4671862ae5b771feab6b`
- **ECR Repo:** `522534289122.dkr.ecr.us-east-1.amazonaws.com/edtech-chatbot`
- **Health URL:** `https://mkbifgscip.us-east-1.awsapprunner.com/api/v1/health`

## Status Commands

```bash
# Frontend — recent deploys (check stage/status)
aws amplify list-jobs --app-id dyio3npn4doy2 --branch-name develop \
  --max-items 3 --query 'jobSummaries[].{Job:jobId,Status:status,Time:endTime,Msg:commitMessage}' \
  --output table --region us-east-1

# Backend — service status
aws apprunner list-services \
  --query 'ServiceSummaryList[?ServiceName==`edtech-chatbot-service-develop`].{Name:ServiceName,Status:Status,URL:ServiceUrl}' \
  --output table --region us-east-1

# Backend — recent operations (deploy history)
aws apprunner list-operations \
  --service-arn "arn:aws:apprunner:us-east-1:522534289122:service/edtech-chatbot-service-develop/1b0e5f1b973c4671862ae5b771feab6b" \
  --max-results 3 --output table --region us-east-1

# ECR — latest image (was it pushed?)
aws ecr describe-images --repository-name edtech-chatbot \
  --query 'sort_by(imageDetails,&imagePushedAt)[-1].{Tags:imageTags,Pushed:imagePushedAt}' \
  --output table --region us-east-1

# Health check
curl -s https://mkbifgscip.us-east-1.awsapprunner.com/api/v1/health

# App Runner logs (last 30 min)
aws logs filter-log-events \
  --log-group-name /aws/apprunner/edtech-chatbot-service-develop/1b0e5f1b973c4671862ae5b771feab6b/application \
  --start-time $(date -v-30M +%s000) --limit 50 --region us-east-1
```

## What to report

```
✅ AGENT DONE: deploy status
Frontend (Amplify):  SUCCEED — job 42 (1 min ago)
Backend  (ECR):      Image pushed — latest + abc1234 (3 min ago)
Backend  (App Runner): RUNNING — last operation SUCCEEDED
Health:              {"status":"ok"}
```

If something is wrong, be specific:
- `⚠️ AGENT ERROR: Frontend build FAILED at BUILD stage — likely npm ci issue`
- `⚠️ AGENT ERROR: ECR has no image newer than 1 hour — CodeBuild may have failed`
- `⚠️ AGENT ERROR: App Runner operation IN_PROGRESS for 10+ min — may be stuck`
- `⚠️ AGENT ERROR: Health check returned non-ok — check App Runner logs`

## Monitor mode

For `"monitor"`: check all stages, sleep 60s, repeat. Stop when:
- Both pipelines show success + health is ok → `✅ AGENT DONE`
- Any stage fails → `⚠️ AGENT ERROR` with details
- 10 checks reached → `ℹ️ AGENT NOTE: timed out, last status: ...`
