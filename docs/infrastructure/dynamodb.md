# DynamoDB

NoSQL database for user data, chat history, and LangGraph conversation state.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     DynamoDB Tables                             │
│                                                                 │
│  ┌─────────────────────────────┐  ┌──────────────────────────┐  │
│  │  EdTechChatbotTable-{env}   │  │ EdTechChatbotCheckpoints │  │
│  │                             │  │        -{env}            │  │
│  │  PK (HASH) │ SK (RANGE)     │  │                          │  │
│  │  ──────────┼────────────    │  │  PK (HASH) │ SK (RANGE)  │  │
│  │  USER#123  │ PROFILE        │  │  ──────────┼──────────── │  │
│  │  USER#123  │ TOKEN#abc      │  │  thread_id │ checkpoint  │  │
│  │  USER#123  │ CONV#xyz       │  │                          │  │
│  │                             │  │  (LangGraph managed)     │  │
│  │  GSI1: email lookup         │  │                          │  │
│  │  TTL: expires_at            │  │                          │  │
│  └─────────────────────────────┘  └──────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

## AWS Resources

| Resource | Value |
|----------|-------|
| **Region** | `us-east-1` |
| **Billing Mode** | PAY_PER_REQUEST (on-demand) |
| **Main Table** | `EdTechChatbotTable-{local,sandbox,prod}` |
| **Checkpoint Table** | `EdTechChatbotCheckpoints-{local,sandbox,prod}` |

## Table Schema

### Main Table

| Attribute | Type | Description |
|-----------|------|-------------|
| `PK` | String | Partition key (e.g., `USER#123`) |
| `SK` | String | Sort key (e.g., `PROFILE`, `TOKEN#abc`) |
| `GSI1PK` | String | GSI partition key (e.g., `EMAIL#user@example.com`) |
| `GSI1SK` | String | GSI sort key |
| `expires_at` | Number | TTL timestamp for auto-deletion |

**Global Secondary Index (GSI1):**
- Used for email-based user lookups during authentication
- Projection: ALL (all attributes copied to index)

**TTL (Time-To-Live):**
- Attribute: `expires_at`
- Used for automatic refresh token deletion after expiry

### Checkpoint Table

| Attribute | Type | Description |
|-----------|------|-------------|
| `PK` | String | Thread ID |
| `SK` | String | Checkpoint identifier |

This table is managed by `langgraph-checkpoint-aws` for conversation state persistence.

## Environment Configuration

### Local Development

DynamoDB Local runs in Docker (port 8001):

```yaml
# docker-compose.yml
dynamodb-local:
  image: amazon/dynamodb-local:latest
  ports:
    - "8001:8000"
  volumes:
    - dynamodb_data:/home/dynamodblocal/data
```

**Connection:**
```
Endpoint: http://localhost:8001
Credentials: dummy (any value works)
```

### Sandbox/Production

Uses AWS-managed DynamoDB with real credentials.

## Common Operations

### Initialize Tables

```bash
# Create tables (inside Docker)
docker compose exec backend python init_db.py

# Or with explicit command
docker compose exec backend python init_db.py create
```

### Reset Tables (Delete + Recreate)

```bash
docker compose exec backend python init_db.py reset
```

### Delete Tables

```bash
docker compose exec backend python init_db.py delete
```

### List Tables (Local)

```bash
aws dynamodb list-tables --endpoint-url http://localhost:8001
```

### Scan Table Contents (Local)

```bash
aws dynamodb scan \
  --table-name EdTechChatbotTable-local \
  --endpoint-url http://localhost:8001
```

### Query by User (Local)

```bash
aws dynamodb query \
  --table-name EdTechChatbotTable-local \
  --key-condition-expression "PK = :pk" \
  --expression-attribute-values '{":pk": {"S": "USER#123"}}' \
  --endpoint-url http://localhost:8001
```

### Check Table Status (AWS)

```bash
aws dynamodb describe-table \
  --table-name EdTechChatbotTable-sandbox \
  --region us-east-1
```

## Code References

| File | Purpose |
|------|---------|
| `backend/app/database.py` | DynamoDB resource initialization |
| `backend/init_db.py` | Table creation/deletion scripts |
| `backend/app/config.py` | Environment-based configuration |
| `backend/app/services/auth_service.py` | User authentication (DynamoDB) |
| `backend/app/services/chat_history_service.py` | Chat history storage |
| `backend/app/graph/graph.py` | LangGraph checkpoint integration |

## Dependencies

```
boto3==1.40.49
aioboto3==15.4.0
langgraph-checkpoint-aws>=1.0.0
```

## Troubleshooting

### "Table not found" errors

Tables must be created after Docker rebuild:
```bash
docker compose down && docker compose up -d --build
docker compose exec backend python init_db.py
```

### DynamoDB Local not starting

Check if port 8001 is in use:
```bash
lsof -i :8001
```

### GSI not returning results

Ensure items have `GSI1PK` and `GSI1SK` attributes set. Items without these won't appear in GSI queries.
