# Project Instructions for Claude

## After Docker Rebuild

After running `docker compose up -d --build` or `docker compose down && docker compose up -d`, always initialize the database:

```bash
docker compose exec backend python init_db.py
```

This creates the DynamoDB tables in the local container. Without this, API requests will fail with 500 errors.
