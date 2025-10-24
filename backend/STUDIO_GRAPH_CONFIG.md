# LangGraph Studio Configuration

**Date**: 2025-10-23
**Status**: Single graph configuration (complete_routing only)

---

## Current Configuration

### LangGraph Studio Graph

Only **one graph** is configured in `langgraph.json`:

```json
{
  "graphs": {
    "complete_routing": "app.chatbot.studio.studio_router:studio_router"
  }
}
```

### Graph Structure

**`complete_routing`** - Complete educational routing system with actual bot implementations

**Flow**:
```
START
  → classify_intent (keyword-based classification)
  → [CONFIDENCE CHECK]
      ├─ High confidence (≥0.5) → route_to_bot → [SPECIALIST ROUTING]
      │                                              ├─ handwriting → execute_handwriting_bot (ACTUAL BOT)
      │                                              ├─ vocabulary → execute_vocabulary_bot (demo)
      │                                              ├─ ideas → execute_ideas_bot (demo)
      │                                              └─ general → execute_general_bot (ACTUAL BOT)
      │
      └─ Low confidence (<0.5) → execute_general_bot (ACTUAL BOT)
  → END
```

---

## Bot Implementations

### ✅ **Actual Bot Implementations** (calls real graphs):

1. **Handwriting Bot** (`execute_handwriting_bot`)
   - Calls: `app.chatbot.specialists.handwriting.graph:run_handwriting_bot`
   - Uses: OpenAI GPT-4o, DynamoDB Forms A-H
   - Full 5-node graph: analyze → retrieve → generate → quality_check → follow_up

2. **General Bot** (`execute_general_bot`)
   - Calls: `app.chatbot.specialists.general.bot:GeneralBot`
   - Uses: OpenAI GPT-4o, cross-domain knowledge
   - Handles low-confidence queries and clarifications

### 📋 **Demo Implementations** (hardcoded responses):

3. **Vocabulary Bot** (`execute_vocabulary_bot`)
   - Hardcoded demo response
   - No API calls
   - Forms I-L reference

4. **Ideas Bot** (`execute_ideas_bot`)
   - Hardcoded demo response
   - No API calls
   - Forms M-Q reference

---

## Intent Classification (Mock)

The `classify_intent` node uses **keyword matching** (not OpenAI):

```python
# Handwriting keywords
["letter", "handwriting", "write", "pencil", "grip", "formation", "stroke"]
→ intent="handwriting", confidence=0.9

# Vocabulary keywords
["word", "vocabulary", "spelling", "reading", "phonics", "sight"]
→ intent="vocabulary", confidence=0.85

# Ideas keywords
["story", "creative", "ideas", "brainstorm", "narrative", "writing"]
→ intent="ideas", confidence=0.8

# Greetings
["hi", "hello", "hey"] (≤3 words)
→ intent="general", confidence=0.8

# General/unclear
→ intent="general", confidence=0.3
```

---

## Confidence-Based Routing

| Confidence | Routing Decision |
|------------|------------------|
| **≥ 0.7** | High confidence → Route to specialist bot directly |
| **0.5 - 0.7** | Medium confidence → Route to specialist with caution |
| **< 0.5** | Low confidence → Route to general bot for clarification |

---

## Testing in LangGraph Studio

### Start LangGraph Studio:
```bash
cd backend
langgraph dev
```

### Sample Queries:

**Handwriting (High Confidence)**:
- "How do I teach letter Z?"
- "Help with handwriting grip"
- "Letter formation strategies"

**Vocabulary (High Confidence)**:
- "Phonics activities for reading"
- "Teaching sight words"
- "Spelling strategies"

**Ideas (High Confidence)**:
- "Creative writing prompts"
- "Story brainstorming ideas"
- "Narrative development"

**Low Confidence (→ General Bot)**:
- "Help me teach"
- "I need assistance"
- "What should I do?"

---

## Environment Variables Required

Make sure `.env.local` has:

```bash
OPENAI_API_KEY=your_key_here
AWS_ACCESS_KEY_ID=your_key_here
AWS_SECRET_ACCESS_KEY=your_key_here
AWS_REGION=us-east-1
DYNAMODB_TABLE_NAME=your_table_name
```

**Note**: Handwriting and General bots will fail without proper credentials.

---

## Troubleshooting

### Issue: Graph hangs/loading forever

**Possible causes**:
1. Missing OpenAI API key → Handwriting/General bot timeout
2. DynamoDB not accessible → Form retrieval timeout
3. Async function blocking

**Solution**: Check terminal logs for error messages

### Issue: Empty responses

**Possible causes**:
1. API call failed silently
2. Message extraction logic issue

**Solution**: Look for `❌ Error in handwriting bot:` or `❌ Error in studio general bot:` in logs

---

## File Locations

- **Graph definition**: `app/chatbot/studio/studio_router.py`
- **Configuration**: `langgraph.json`
- **Handwriting bot**: `app/chatbot/specialists/handwriting/graph.py`
- **General bot**: `app/chatbot/specialists/general/bot.py`
- **Routing state**: `app/chatbot/routing/router_state.py`

---

## What Was Removed

The following graphs were removed from `langgraph.json`:

- ❌ `lesson_planner` (demo graph)
- ❌ `handwriting_bot` (direct access to handwriting graph)

Now only `complete_routing` is available, which shows the full routing flow and uses actual bot implementations.