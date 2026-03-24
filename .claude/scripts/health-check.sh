#!/bin/bash
# Health check for EdTech chatbot — single source of truth
# Used by: /dev health (via Claude), post-deploy hook (background)

REGION="us-east-1"
ENV_FILE="$(dirname "$0")/../../backend/.env"

# Backend API
BACKEND=$(curl -s -o /dev/null -w "%{http_code}" https://mkbifgscip.us-east-1.awsapprunner.com/api/v1/health 2>/dev/null)

# Frontend
FRONTEND=$(curl -s -o /dev/null -w "%{http_code}" https://composeearly.com 2>/dev/null)

# OpenAI key validation
if [ -f "$ENV_FILE" ]; then
  OPENAI=$(source "$ENV_FILE" && curl -s -w "\n%{http_code}" https://api.openai.com/v1/models \
    -H "Authorization: Bearer $OPENAI_API_KEY" 2>/dev/null | tail -1)
else
  OPENAI="no .env"
fi

# App Runner status
APPRUNNER=$(aws apprunner list-services \
  --query 'ServiceSummaryList[?ServiceName==`edtech-chatbot-service-develop`].Status' \
  --output text --region "$REGION" 2>/dev/null)

# DynamoDB
DYNAMO=$(aws dynamodb describe-table --table-name EdTechChatbotTable-sandbox \
  --query 'Table.TableStatus' --output text --region "$REGION" 2>/dev/null)

# Format results
ISSUES=0
result() {
  local name="$1" value="$2" expected="$3"
  if [ "$value" = "$expected" ]; then
    printf "%-12s ✅ %s\n" "$name:" "$value"
  else
    printf "%-12s ⚠️  %s\n" "$name:" "$value"
    ISSUES=$((ISSUES + 1))
  fi
}

result "Backend"    "$BACKEND"   "200"
result "Frontend"   "$FRONTEND"  "200"
if [ "$OPENAI" = "200" ]; then
  result "OpenAI key" "valid" "valid"
else
  result "OpenAI key" "$OPENAI" "200"
fi
result "App Runner" "$APPRUNNER" "RUNNING"
result "DynamoDB"   "$DYNAMO"    "ACTIVE"

exit $ISSUES
