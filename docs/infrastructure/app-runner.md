# App Runner & ECR

Backend compute service with container registry. ECR stores Docker images; App Runner runs them with auto-scaling.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              Deployment Flow                                │
│                                                                             │
│  ┌──────────┐     ┌───────────┐     ┌─────────┐     ┌──────────────────┐   │
│  │  GitHub  │────▶│ CodeBuild │────▶│   ECR   │────▶│    App Runner    │   │
│  │  Push    │     │  (Build)  │     │ (Store) │     │  (Auto-deploy)   │   │
│  └──────────┘     └───────────┘     └─────────┘     └──────────────────┘   │
│                                                              │              │
│                                                              ▼              │
│                                                     https://mkbifgscip     │
│                                                     .us-east-1             │
│                                                     .awsapprunner.com      │
└─────────────────────────────────────────────────────────────────────────────┘
```

## AWS Resources

### App Runner Service

| Property | Value |
|----------|-------|
| **Service Name** | `edtech-chatbot-service-develop` |
| **Service ID** | `1b0e5f1b973c4671862ae5b771feab6b` |
| **Service URL** | `https://mkbifgscip.us-east-1.awsapprunner.com` |
| **Status** | RUNNING |
| **Region** | `us-east-1` |
| **Created** | 2025-09-26 |

### ECR Repository

| Property | Value |
|----------|-------|
| **Repository** | `edtech-chatbot` |
| **URI** | `522534289122.dkr.ecr.us-east-1.amazonaws.com/edtech-chatbot` |
| **Image Tag** | `latest` (auto-deployed) |

## Service Configuration

### Compute

| Property | Value |
|----------|-------|
| **CPU** | 0.5 vCPU (512 units) |
| **Memory** | 1 GB (1024 MB) |
| **Port** | 8000 |

### Auto-Deploy

Auto-deployment is **enabled**. When a new image is pushed to ECR with the `latest` tag, App Runner automatically deploys it.

### Health Check

| Property | Value |
|----------|-------|
| **Protocol** | HTTP |
| **Path** | `/api/v1/health` |
| **Interval** | 10 seconds |
| **Timeout** | 5 seconds |
| **Healthy Threshold** | 1 |
| **Unhealthy Threshold** | 5 |

### Auto-Scaling

Using `DefaultConfiguration`:
- Scales based on concurrent requests
- Min/max instances managed by AWS defaults

### Network

| Property | Value |
|----------|-------|
| **Egress** | DEFAULT (public internet access) |
| **Ingress** | Publicly accessible |
| **IP Type** | IPv4 |

## Environment Variables

### Plaintext (in service config)

| Variable | Value |
|----------|-------|
| `APP_ENV` | `sandbox` |
| `DYNAMODB_TABLE_NAME` | `EdTechChatbotTable` |
| `FRONTEND_URL` | `https://composeearly.com,https://www.composeearly.com` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | `7` |

### Secrets (via Secrets Manager)

| Variable | Secret ARN |
|----------|------------|
| `OPENAI_API_KEY` | `edtech-chatbot/test/openai` |

## IAM Roles

| Role | Purpose |
|------|---------|
| `AppRunnerECRAccessRole` | Allows App Runner to pull images from ECR |
| `AppRunner-Service-Role-SecretsReadWrite` | Instance role for Secrets Manager access |

## Common Operations

### Check Service Status

```bash
aws apprunner list-services --region us-east-1
```

### Get Service Details

```bash
aws apprunner describe-service \
  --service-arn "arn:aws:apprunner:us-east-1:522534289122:service/edtech-chatbot-service-develop/1b0e5f1b973c4671862ae5b771feab6b" \
  --region us-east-1
```

### View Deployment Logs

```bash
aws apprunner list-operations \
  --service-arn "arn:aws:apprunner:us-east-1:522534289122:service/edtech-chatbot-service-develop/1b0e5f1b973c4671862ae5b771feab6b" \
  --region us-east-1
```

### Manual Deployment Trigger

```bash
aws apprunner start-deployment \
  --service-arn "arn:aws:apprunner:us-east-1:522534289122:service/edtech-chatbot-service-develop/1b0e5f1b973c4671862ae5b771feab6b" \
  --region us-east-1
```

### Pause Service (Cost Savings)

```bash
aws apprunner pause-service \
  --service-arn "arn:aws:apprunner:us-east-1:522534289122:service/edtech-chatbot-service-develop/1b0e5f1b973c4671862ae5b771feab6b" \
  --region us-east-1
```

### Resume Service

```bash
aws apprunner resume-service \
  --service-arn "arn:aws:apprunner:us-east-1:522534289122:service/edtech-chatbot-service-develop/1b0e5f1b973c4671862ae5b771feab6b" \
  --region us-east-1
```

## ECR Operations

### Login to ECR

```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  522534289122.dkr.ecr.us-east-1.amazonaws.com
```

### List Images

```bash
aws ecr describe-images \
  --repository-name edtech-chatbot \
  --region us-east-1
```

### Push Image Manually

```bash
# Build
docker build -t edtech-chatbot ./backend

# Tag
docker tag edtech-chatbot:latest \
  522534289122.dkr.ecr.us-east-1.amazonaws.com/edtech-chatbot:latest

# Push (triggers auto-deploy)
docker push 522534289122.dkr.ecr.us-east-1.amazonaws.com/edtech-chatbot:latest
```

### Delete Old Images

```bash
aws ecr batch-delete-image \
  --repository-name edtech-chatbot \
  --image-ids imageTag=old-tag \
  --region us-east-1
```

## Code References

| File | Purpose |
|------|---------|
| `backend/Dockerfile` | Container build definition |
| `buildspec.yml` | CodeBuild pipeline (ECR push) |

## Deployment Pipeline

1. **Push to GitHub** → triggers CodeBuild
2. **CodeBuild** runs `buildspec.yml`:
   - Logs into ECR
   - Builds Docker image from `backend/Dockerfile`
   - Tags with `latest` and commit SHA
   - Pushes to ECR
3. **App Runner** detects new `latest` image → auto-deploys

## Troubleshooting

### Deployment stuck in "Operation in progress"

Check recent operations:
```bash
aws apprunner list-operations \
  --service-arn "arn:aws:apprunner:us-east-1:522534289122:service/edtech-chatbot-service-develop/1b0e5f1b973c4671862ae5b771feab6b" \
  --region us-east-1
```

### Health check failing

1. Verify `/api/v1/health` endpoint works locally
2. Check container logs in App Runner console
3. Ensure port 8000 is exposed in Dockerfile

### ECR push denied

Re-authenticate:
```bash
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin \
  522534289122.dkr.ecr.us-east-1.amazonaws.com
```

### Secrets not loading

Ensure `AppRunner-Service-Role-SecretsReadWrite` has `secretsmanager:GetSecretValue` permission for the secret ARNs.

### CORS errors on login or API calls

**Symptom:** Browser console shows `Access-Control-Allow-Origin` errors when calling the API from the deployed frontend.

**Root cause:** The browser's `Origin` header (determined by the URL bar) must exactly match one of the origins in `FRONTEND_URL`. Common mismatches:
- `https://www.composeearly.com` vs `https://composeearly.com` (www vs bare domain)
- `https://develop.dyio3npn4doy2.amplifyapp.com` vs `https://composeearly.com` (Amplify default vs custom domain)

**Fix:**
1. `FRONTEND_URL` supports comma-separated origins (see `backend/app/config.py` `allowed_origins` property)
2. Ensure Amplify has a 301 redirect from `www` → bare domain (see `amplify.md` redirect rules)
3. Update the env var: `FRONTEND_URL=https://composeearly.com,https://www.composeearly.com`

## Security Note

Some environment variables contain sensitive data (AWS keys, SECRET_KEY) in plaintext. Consider migrating these to Secrets Manager for better security. See `secrets-manager.md` for details.
