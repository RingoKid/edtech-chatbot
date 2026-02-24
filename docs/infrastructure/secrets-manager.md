# Secrets Manager

Secure storage for API keys and sensitive credentials used by App Runner.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                      Secrets Manager                            │
│                                                                 │
│  ┌───────────────────────────┐    ┌──────────────────────────┐  │
│  │ edtech-chatbot/test/      │    │      App Runner          │  │
│  │         openai            │───▶│                          │  │
│  │                           │    │  Injects as env vars     │  │
│  └───────────────────────────┘    │  at container startup    │  │
│                                   └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## AWS Resources

| Secret Name | ARN | Last Accessed |
|-------------|-----|---------------|
| `edtech-chatbot/test/openai` | `arn:aws:secretsmanager:us-east-1:522534289122:secret:edtech-chatbot/test/openai-UEeWSK` | 2026-01-06 |

## Naming Convention

```
edtech-chatbot/{environment}/{service}
```

Examples:
- `edtech-chatbot/test/openai` — OpenAI API key for test/sandbox
- `edtech-chatbot/prod/openai` — (future) OpenAI key for production

## App Runner Integration

Secrets are injected via `RuntimeEnvironmentSecrets` in App Runner:

```json
{
  "RuntimeEnvironmentSecrets": {
    "OPENAI_API_KEY": "arn:aws:secretsmanager:us-east-1:522534289122:secret:edtech-chatbot/test/openai-UEeWSK"
  }
}
```

App Runner fetches these at container startup and exposes them as environment variables.

## IAM Requirements

The App Runner instance role (`AppRunner-Service-Role-SecretsReadWrite`) needs:

```json
{
  "Effect": "Allow",
  "Action": [
    "secretsmanager:GetSecretValue"
  ],
  "Resource": [
    "arn:aws:secretsmanager:us-east-1:522534289122:secret:edtech-chatbot/*"
  ]
}
```

## Common Operations

### List Project Secrets

```bash
aws secretsmanager list-secrets \
  --filters Key=name,Values=edtech-chatbot \
  --region us-east-1
```

### Get Secret Value

```bash
aws secretsmanager get-secret-value \
  --secret-id edtech-chatbot/test/openai \
  --region us-east-1
```

### Create New Secret

```bash
aws secretsmanager create-secret \
  --name edtech-chatbot/test/new-service \
  --secret-string "your-api-key-here" \
  --region us-east-1
```

### Update Secret Value

```bash
aws secretsmanager put-secret-value \
  --secret-id edtech-chatbot/test/openai \
  --secret-string "new-api-key-value" \
  --region us-east-1
```

### Rotate Secret (Manual)

```bash
# Update the value
aws secretsmanager put-secret-value \
  --secret-id edtech-chatbot/test/openai \
  --secret-string "new-rotated-key" \
  --region us-east-1

# Trigger App Runner redeployment to pick up new value
aws apprunner start-deployment \
  --service-arn "arn:aws:apprunner:us-east-1:522534289122:service/edtech-chatbot-service-develop/1b0e5f1b973c4671862ae5b771feab6b" \
  --region us-east-1
```

### Delete Secret

```bash
# Schedule deletion (7-30 day recovery window)
aws secretsmanager delete-secret \
  --secret-id edtech-chatbot/test/old-secret \
  --recovery-window-in-days 7 \
  --region us-east-1

# Force immediate deletion (no recovery)
aws secretsmanager delete-secret \
  --secret-id edtech-chatbot/test/old-secret \
  --force-delete-without-recovery \
  --region us-east-1
```

### View Secret Versions

```bash
aws secretsmanager list-secret-version-ids \
  --secret-id edtech-chatbot/test/openai \
  --region us-east-1
```

## Adding a New Secret to App Runner

1. **Create the secret:**
   ```bash
   aws secretsmanager create-secret \
     --name edtech-chatbot/test/new-api \
     --secret-string "api-key-value" \
     --region us-east-1
   ```

2. **Note the ARN** from the output

3. **Update App Runner service** to include the new secret:
   ```bash
   # Via AWS Console: App Runner > Service > Configuration > Edit
   # Add to "Environment secrets" section
   ```

4. **Redeploy** to pick up changes

## Secrets NOT in Secrets Manager (Security Risk)

The following are currently stored as plaintext env vars in App Runner. Consider migrating:

| Variable | Risk Level | Recommendation |
|----------|------------|----------------|
| `AWS_ACCESS_KEY_ID` | High | Use IAM role instead |
| `AWS_SECRET_ACCESS_KEY` | High | Use IAM role instead |
| `SECRET_KEY` | High | Move to Secrets Manager |
| `SPEECHMATICS_API_KEY` | Medium | Move to Secrets Manager |

### Migration Example

```bash
# Create secret
aws secretsmanager create-secret \
  --name edtech-chatbot/test/secret-key \
  --secret-string "d155db39023d182bebd95ba93ca6d148e8a40bd4d112e4cad16d6e64b0661b5b" \
  --region us-east-1

# Then update App Runner to use RuntimeEnvironmentSecrets
# instead of RuntimeEnvironmentVariables for this value
```

## Cost

- **Storage**: $0.40 per secret per month
- **API calls**: $0.05 per 10,000 API calls
- Current usage: ~$0.40/month (1 secret)

## Related Docs

- `app-runner.md` — Service that consumes these secrets
