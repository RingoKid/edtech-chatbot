#!/bin/bash
# n8n API wrapper - sources env and calls API
# Usage: ./n8n/api.sh <endpoint> [curl-args...]
# Example: ./n8n/api.sh workflows
#          ./n8n/api.sh workflows/abc123 -X DELETE

set -e
source "$(dirname "$0")/../backend/.env.local"

ENDPOINT="${1:-workflows}"
shift 2>/dev/null || true

curl -s "http://localhost:5678/api/v1/$ENDPOINT" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  "$@"
