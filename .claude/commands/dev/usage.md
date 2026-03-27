---
description: Check usage data — user counts, conversations, feedback, traffic, and errors
---

# /dev usage

**Run mode:** inline. Run the commands below, aggregate results, and present a usage dashboard.

## Arguments

`$ARGUMENTS` — number of days to look back:

- (empty) → Last 7 days (default)
- `1` → Last 24 hours
- `14` → Last 14 days
- `30` → Last 30 days
- Any number → That many days

Parse the first number from the arguments. If no number found, default to 7.

## AWS Identifiers

- **Region:** us-east-1
- **DynamoDB Table:** `EdTechChatbotTable-sandbox`
- **App Runner Service Name:** `edtech-chatbot-service-develop`
- **App Runner Service ID:** `1b0e5f1b973c4671862ae5b771feab6b`
- **App Runner Log Group:** `/aws/apprunner/edtech-chatbot-service-develop/1b0e5f1b973c4671862ae5b771feab6b/application`
- **CloudWatch Dashboard:** https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=EdTechChatbot

## Step 1: DynamoDB Data

Run a single full scan and split with jq (avoids filter-expression special chars that break permission patterns):

```bash
aws dynamodb scan --table-name EdTechChatbotTable-sandbox --region us-east-1 --output json | jq '{
  users: [.Items[] | select(.PK.S | startswith("USER#")) | select(.SK.S == "PROFILE") |
    {user_id: .user_id.S, email: .email.S, full_name: .full_name.S, role: .role.S, created_at: .created_at.S}],
  conversations: [.Items[] | select(.SK.S | startswith("THREAD#")) |
    {pk: .PK.S, thread_id: .thread_id.S, title: .title.S, created_at: .created_at.S, updated_at: .updated_at.S}],
  feedback: [.Items[] | select(.SK.S | startswith("FEEDBACK#")) |
    {task_type: .task_type.S, category: .category.S, rating: (.rating.N // null), created_at: .created_at.S}]
}'
```

**Aggregate from the JSON results:**
- Total users, admins vs regular (check `role` field)
- Recent signups (sort by `created_at`, show last 5)
- Total conversations, conversations in the time period (compare `created_at` to date threshold)
- Avg conversations per user (total convos / total users)
- Total feedback, avg rating (from `rating` field, ignore 0s and nulls), group by `task_type`

## Step 2: CloudWatch Traffic Metrics

Use the number of days (N) from arguments. Calculate `--start-time` as N days ago and `--period` as 86400 (daily).

```bash
# Requests
aws cloudwatch get-metric-statistics \
  --namespace AWS/AppRunner \
  --metric-name Requests \
  --dimensions Name=ServiceName,Value=edtech-chatbot-service-develop Name=ServiceID,Value=1b0e5f1b973c4671862ae5b771feab6b \
  --start-time $(date -u -v-{N}d +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 --statistics Sum \
  --region us-east-1

# 2xx
aws cloudwatch get-metric-statistics \
  --namespace AWS/AppRunner \
  --metric-name 2xxStatusResponses \
  --dimensions Name=ServiceName,Value=edtech-chatbot-service-develop Name=ServiceID,Value=1b0e5f1b973c4671862ae5b771feab6b \
  --start-time $(date -u -v-{N}d +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 --statistics Sum \
  --region us-east-1

# 4xx
aws cloudwatch get-metric-statistics \
  --namespace AWS/AppRunner \
  --metric-name 4xxStatusResponses \
  --dimensions Name=ServiceName,Value=edtech-chatbot-service-develop Name=ServiceID,Value=1b0e5f1b973c4671862ae5b771feab6b \
  --start-time $(date -u -v-{N}d +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 --statistics Sum \
  --region us-east-1

# 5xx
aws cloudwatch get-metric-statistics \
  --namespace AWS/AppRunner \
  --metric-name 5xxStatusResponses \
  --dimensions Name=ServiceName,Value=edtech-chatbot-service-develop Name=ServiceID,Value=1b0e5f1b973c4671862ae5b771feab6b \
  --start-time $(date -u -v-{N}d +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 --statistics Sum \
  --region us-east-1

# Latency
aws cloudwatch get-metric-statistics \
  --namespace AWS/AppRunner \
  --metric-name RequestLatency \
  --dimensions Name=ServiceName,Value=edtech-chatbot-service-develop Name=ServiceID,Value=1b0e5f1b973c4671862ae5b771feab6b \
  --start-time $(date -u -v-{N}d +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 86400 --statistics Average \
  --region us-east-1
```

**Aggregate:** Sum all datapoints for totals. Calculate error rate = `(4xx + 5xx) / total * 100`.

## Step 3: Error Logs (only if 4xx or 5xx > 0)

Skip this step entirely if there are zero 4xx and 5xx responses.

```bash
# Fetch recent error logs
aws logs filter-log-events \
  --log-group-name /aws/apprunner/edtech-chatbot-service-develop/1b0e5f1b973c4671862ae5b771feab6b/application \
  --start-time $(date -u -v-{N}d +%s000) \
  --filter-pattern "?ERROR ?Traceback" \
  --limit 20 --region us-east-1
```

Summarize the error patterns — group similar errors and count them.

## Output Format

Present as a clean dashboard:

```
📊 Usage Report (last N days)
═══════════════════════════════════════

👥 Users
   Total: 12 (2 admins, 10 regular)
   Recent signups:
     • jane@gsu.edu — Mar 25
     • john@gsu.edu — Mar 20

💬 Conversations
   Total: 87
   Last N days: 23
   Avg per user: 7.3

⭐ Feedback
   Total: 34 | Avg rating: 4.2/5
   Handwriting: 18 | Vocabulary: 10 | Idea Gen: 6

🌐 Traffic (last N days)
   Total requests: 1,247
   ✅ 2xx: 1,190 (95.4%)
   ⚠️ 4xx: 52 (4.2%)
   🔴 5xx: 5 (0.4%)
   Avg latency: 342ms

   Daily breakdown:
     Mar 25: 198 req | Mar 24: 287 req | Mar 23: 312 req | ...

🔗 Dashboard: https://us-east-1.console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=EdTechChatbot
```

If there are errors, add:

```
🚨 Errors (5 occurrences)
   • ValueError: invalid token (3x)
   • TimeoutError: DynamoDB read (2x)
```

## Notes

- Run DynamoDB scans and CloudWatch calls in parallel where possible (use multiple Bash calls)
- If a scan returns 0 items, still show the section with 0 counts
- If CloudWatch returns no datapoints, note "no traffic recorded" for that period
- Format numbers with commas for readability (1,247 not 1247)
- Sort daily breakdown most recent first
