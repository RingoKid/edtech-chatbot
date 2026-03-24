#!/bin/bash
# Post-deploy monitor — polls App Runner until deploy completes, then runs health check
# Triggered by PostToolUse hook on "git push ... develop"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
ARN="arn:aws:apprunner:us-east-1:522534289122:service/edtech-chatbot-service-develop/1b0e5f1b973c4671862ae5b771feab6b"
REGION="us-east-1"
MAX_ATTEMPTS=10
INTERVAL=60
LOG="/tmp/claude-deploy-health.log"

echo "$(date) — Deploy health check started" > "$LOG"
echo "$(date) — Waiting 90s for CodeBuild to trigger..." >> "$LOG"
osascript -e 'display notification "Deploy monitor started — waiting 90s for build..." with title "🚀 Deploy"' 2>/dev/null
sleep 90

# Poll App Runner until deployment completes
for i in $(seq 1 $MAX_ATTEMPTS); do
  STATUS=$(aws apprunner list-operations --service-arn "$ARN" --max-results 1 \
    --query 'OperationSummaryList[0].Status' --output text --region "$REGION" 2>&1)

  echo "$(date) — Poll $i/$MAX_ATTEMPTS: $STATUS" >> "$LOG"
  osascript -e "display notification \"Poll $i/$MAX_ATTEMPTS: $STATUS\" with title \"🔄 Deploy Monitor\"" 2>/dev/null

  if [ "$STATUS" = "SUCCEEDED" ]; then
    break
  elif [ "$STATUS" = "FAILED" ]; then
    echo "$(date) — ⚠️ App Runner deployment FAILED" >> "$LOG"
    osascript -e 'display notification "App Runner deployment FAILED" with title "⚠️ Deploy Health"' 2>/dev/null
    exit 1
  fi

  if [ "$i" -eq "$MAX_ATTEMPTS" ]; then
    echo "$(date) — Timed out after $MAX_ATTEMPTS checks, running health check anyway" >> "$LOG"
  else
    sleep $INTERVAL
  fi
done

# Run health check
echo "" >> "$LOG"
echo "$(date) — Running health checks..." >> "$LOG"
RESULT=$("$SCRIPT_DIR/health-check.sh" 2>&1)
EXIT_CODE=$?
echo "$RESULT" >> "$LOG"

# macOS notification
if [ $EXIT_CODE -eq 0 ]; then
  osascript -e 'display notification "All systems green ✅" with title "Deploy Health Check"' 2>/dev/null
else
  osascript -e 'display notification "Issues detected — check /tmp/claude-deploy-health.log" with title "⚠️ Deploy Health"' 2>/dev/null
fi
