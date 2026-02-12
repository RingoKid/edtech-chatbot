# 017: Feedback Collector

## Implementation Status

| Component                     | Status | Notes                                      |
| ----------------------------- | ------ | ------------------------------------------ |
| Feedback collector agent      | ✅ Done | `app/graph/agents/feedback_collector.py`   |
| `submit_feedback` tool        | ✅ Done | Extracts structured feedback from user     |
| `skip_feedback` tool          | ✅ Done | User declines to leave feedback            |
| FeedbackService               | ✅ Done | `app/services/feedback_service.py`         |
| Feedback model                | ✅ Done | `app/models.py`                            |
| GraphState update             | ✅ Done | `feedback_submitted`, `FeedbackData` added |
| Graph routing update          | ✅ Done | Generator → feedback_collector → END       |
| DB schema update              | ✅ Done | `FEEDBACK_KEY_PATTERNS` in `db_schema.py`  |
| init_db.py update             | ✅ Done | `validate_table_support()` verifies GSI1   |
| ChatService integration       | ✅ Done | Persists feedback after graph invocation   |
| Unit test: FeedbackService    | ✅ Done | 4/4 passing                                |
| Node eval: feedback_collector | ✅ Done | 5/5 passing                                |
| E2E test script               | ✅ Done | Full flow verified                         |

## Overview

**Status:** Implemented
**Layer:** Post-generation (after Layer 3 generators)
**Model:** `gpt-4o-mini` (lightweight parsing task)
**Framework:** `create_agent` from `langchain.agents` (LangGraph 1.0+)

ReAct agent that collects optional user feedback after lesson generation. Runs after any generator calls `finalize_lesson()`. Parses user feedback into structured data (category, rating, text) and persists to DynamoDB separately from the checkpointer.

---

## Architecture Context

```
                    FROM ANY GENERATOR
                    (finalize_lesson called)
                           │
                           │ state.lesson_finalized = True
                           ▼
┌─────────────────────────────────────────────────────────────┐
│            Feedback Collector Agent (THIS SPEC)              │
│                                                             │
│  Reads: conversation history (for context)                  │
│  Tools: submit_feedback(), skip_feedback()                  │
│                                                             │
│  Flow:                                                      │
│  1. Ask user for optional feedback                          │
│  2. Parse response → call appropriate tool                  │
│  3. ChatService persists feedback_data to DynamoDB          │
│  4. feedback_submitted = True → END                         │
└─────────────────────────────────────────────────────────────┘
```

### Same-Invocation Handoff (Turn where user finalizes)

When the user says "Looks good" to the generator, both nodes run in a single `ainvoke`:

```
ainvoke("Looks good")
  │
  ├─ 1. handwriting_generator runs
  │     → calls finalize_lesson()
  │     → lesson_finalized = True
  │
  ├─ 2. route_after_handwriting_generator
  │     → lesson_finalized → "feedback_collector"
  │
  └─ 3. feedback_collector runs
        → asks "Any feedback about the lesson or platform?"
        → END (graph completes, waits for next user message)
```

User sees the feedback prompt in the same response as the finalization.

### Next-Invocation Feedback Processing (Turn where user gives feedback)

```
ainvoke("Great lesson, 5 stars")
  │
  ├─ 1. entry_router
  │     → lesson_finalized=True, feedback_submitted=False
  │     → "feedback_collector"
  │
  └─ 2. feedback_collector runs
        → parses "Great lesson, 5 stars"
        → calls submit_feedback(category="lesson", rating=5, text="Great lesson")
        → feedback_submitted = True → END
```

ChatService then reads `feedback_data` from the result and persists to DynamoDB.

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Agent type | ReAct agent | Consistent with other agents in the system |
| Model | `gpt-4o-mini` | Lightweight parsing task, no complex generation |
| Storage location | Existing main DynamoDB table | Single-table design, GSI1 already supports user queries |
| Key pattern | `PK=THREAD#, SK=FEEDBACK#` | Query all feedback for a thread |
| Persistence trigger | ChatService (after `ainvoke`) | Graph stays stateless; `thread_id` and `user_id` available in ChatService |
| Rating | Optional (1-5) | Extract if user provides one, don't force it |
| Category | `lesson` / `platform` / `general` | Broad enough to cover expected feedback types |
| Feedback optional | Yes | User can skip; don't block the flow |

---

## DynamoDB Schema

### Key Patterns (existing main table — `EdTechChatbotTable-{env}`)

```
# Feedback record
PK:     THREAD#{thread_id}
SK:     FEEDBACK#{feedback_id}

# GSI1 — query feedback by user
GSI1PK: USER#{user_id}
GSI1SK: FEEDBACK#{created_at}
```

No schema changes needed — the existing table's `PK/SK + GSI1` already supports these key patterns. Feedback records use new PK/SK prefixes alongside existing User, Conversation, and RefreshToken entities.

### Attributes

| Attribute | Type | Description |
|-----------|------|-------------|
| `PK` | S | `THREAD#{thread_id}` |
| `SK` | S | `FEEDBACK#{feedback_id}` |
| `GSI1PK` | S | `USER#{user_id}` |
| `GSI1SK` | S | `FEEDBACK#{created_at}` |
| `type` | S | `"Feedback"` |
| `feedback_id` | S | UUID |
| `thread_id` | S | Thread this feedback belongs to |
| `user_id` | S | User who submitted feedback |
| `task_type` | S | `"handwriting"` / `"vocabulary"` / `"idea_generation"` |
| `category` | S | `"lesson"` / `"platform"` / `"general"` |
| `rating` | N | 1-5 (optional — omitted if not provided) |
| `text` | S | Free-text feedback |
| `created_at` | S | ISO 8601 timestamp |

### Query Patterns

| Query | Access Pattern |
|-------|---------------|
| Feedback for a conversation | `PK = THREAD#{thread_id}, SK begins_with FEEDBACK#` |
| All feedback by a user | GSI1: `GSI1PK = USER#{user_id}, GSI1SK begins_with FEEDBACK#` |
| Trace to full conversation | Use `thread_id` → checkpointer or `/chat/{thread_id}/messages` |

### init_db.py Changes

1. Add `FEEDBACK_KEY_PATTERNS` documentation constant to `db_schema.py`
2. Add `validate_table_support()` function to `init_db.py` — verifies GSI1 exists on main table (required for feedback user queries)
3. Call validation after table creation in `main()`

---

## Tool Definitions

### submit_feedback

Extracts structured feedback from the user's message.

| Property | Value |
|----------|-------|
| Name | `submit_feedback` |
| Parameters | `category` (str), `rating` (int), `text` (str) |
| Behavior | Returns confirmation string |

The LLM calls this tool with parsed fields. The tool itself just returns a confirmation. The `feedback_collector_node` extracts the tool call arguments into `feedback_data` in state. ChatService then persists to DynamoDB.

### skip_feedback

User declines to leave feedback.

| Property | Value |
|----------|-------|
| Name | `skip_feedback` |
| Parameters | None |
| Behavior | Returns skip confirmation |

---

## State Changes

### GraphState additions

```python
# Signals that feedback has been submitted or skipped
feedback_submitted: bool  # default False

# Structured feedback data extracted by the feedback collector
# Persisted to DynamoDB by ChatService after graph invocation
feedback_data: Optional[FeedbackData]  # default None
```

### FeedbackData TypedDict

```python
class FeedbackData(TypedDict):
    category: str         # "lesson" | "platform" | "general"
    rating: Optional[int] # 1-5 or None
    text: str             # Free-text feedback
```

---

## Agent Behavior

### System Prompt

```
You are a feedback collector for an educational lesson planning platform.

The user just finished generating a lesson. Your job is to ask for optional
feedback and process their response.

## Rules

1. Ask ONE brief question: "Before we wrap up, do you have any feedback
   about the lesson or the platform? You can also say 'skip' to finish."

2. If the user provides feedback, call submit_feedback with:
   - category: "lesson" (about the generated content), "platform" (about
     the app/UX), or "general" (mixed or unclear)
   - rating: Extract a 1-5 rating if the user mentions one. Examples:
     "5 stars" → 5, "8/10" → 4, "terrible" → 1. If no rating mentioned,
     use 0 to indicate no rating.
   - text: The user's feedback in their own words

3. If the user says "skip", "no", "I'm good", "no thanks", etc.,
   call skip_feedback

4. Be brief. Don't ask follow-up questions after the initial ask.
```

### Expected Behaviors

| Scenario | Agent Does |
|----------|------------|
| First run (after finalize) | Ask for feedback |
| "Great lesson, 5 stars!" | `submit_feedback(category="lesson", rating=5, text="Great lesson")` |
| "The app is a bit slow" | `submit_feedback(category="platform", rating=0, text="The app is a bit slow")` |
| "Good lesson but hard to navigate" | `submit_feedback(category="general", rating=0, text="Good lesson but hard to navigate")` |
| "No thanks" / "Skip" / "I'm good" | `skip_feedback()` |

---

## Graph Changes

### Routing Updates

```python
# After handwriting generator (CHANGED — was always END)
def route_after_handwriting_generator(state: GraphState) -> str:
    if state.get("lesson_finalized"):
        return "feedback_collector"
    return END

# After feedback collector (NEW)
def route_after_feedback_collector(state: GraphState) -> str:
    return END

# Entry router (UPDATED — add feedback_collector case)
def entry_router(state: GraphState) -> str:
    # Existing: mid-generation
    if (
        state.get("handwriting_params") is not None
        and not state.get("lesson_finalized", False)
    ):
        return "handwriting_generator"

    # NEW: mid-feedback (finalized but feedback not yet submitted)
    if (
        state.get("lesson_finalized", False)
        and not state.get("feedback_submitted", False)
    ):
        return "feedback_collector"

    return "routing_agent"
```

### Graph Edges

```python
# New node
graph.add_node("feedback_collector", feedback_collector_node)

# Updated handwriting generator edges
graph.add_conditional_edges(
    "handwriting_generator",
    route_after_handwriting_generator,
    {
        "feedback_collector": "feedback_collector",
        END: END,
    }
)

# New feedback collector edges
graph.add_conditional_edges(
    "feedback_collector",
    route_after_feedback_collector,
    {END: END}
)

# Updated entry router map
graph.set_conditional_entry_point(
    entry_router,
    {
        "routing_agent": "routing_agent",
        "handwriting_generator": "handwriting_generator",
        "feedback_collector": "feedback_collector",
    }
)
```

---

## ChatService Integration

After `graph.ainvoke` returns, ChatService checks for feedback data and persists it.

Location: `app/services/chat_service.py` → `handle_message()`, after the existing conversation metadata updates.

```python
# After graph.ainvoke returns result:
feedback_data = result.get("feedback_data")
if feedback_data:
    feedback_service = get_feedback_service()
    await feedback_service.save_feedback(
        thread_id=thread_id,
        user_id=user_id,
        task_type=result.get("task_type", "unknown"),
        category=feedback_data["category"],
        rating=feedback_data.get("rating"),
        text=feedback_data["text"],
    )
```

This keeps the graph layer auth-agnostic — `user_id` and `thread_id` are available in ChatService but never added to GraphState.

---

## Implementation Files

### New Files

| File | Purpose |
|------|---------|
| `app/graph/agents/feedback_collector.py` | Feedback collector agent + tools |
| `app/services/feedback_service.py` | DynamoDB feedback read/write |
| `tests/unit/test_feedback_service.py` | Unit tests for FeedbackService |
| `tests/evals/test_feedback_collector.py` | Node-level eval tests |
| `scripts/test_feedback_e2e.py` | E2E smoke test script |

### Modified Files

| File | Changes |
|------|---------|
| `app/graph/state.py` | Add `feedback_submitted`, `FeedbackData` |
| `app/graph/graph.py` | Add feedback_collector node, update routing, update entry_router |
| `app/services/chat_service.py` | Persist feedback after graph invocation |
| `app/db_schema.py` | Add `FEEDBACK_KEY_PATTERNS` documentation |
| `scripts/init_db.py` | Add `validate_table_support()` function |
| `app/models.py` | Add `Feedback` Pydantic model |

---

## Verification

### Unit Tests (no LLM, fast)

```bash
docker compose exec backend pytest tests/unit/test_feedback_service.py -v
```

| Test | Verifies |
|------|----------|
| `test_save_feedback` | Write feedback record, verify all DynamoDB attributes |
| `test_get_feedback_by_thread` | Query by `PK = THREAD#{thread_id}` returns correct records |
| `test_get_feedback_by_user` | GSI1 query by `USER#{user_id}` returns correct records |
| `test_save_feedback_without_rating` | Rating field omitted when not provided |

### Node-Level Evals (LLM, medium)

```bash
docker compose exec backend pytest tests/evals/test_feedback_collector.py -v
```

| Test | Input | Expected |
|------|-------|----------|
| `test_positive_feedback` | "Great lesson!" | `submit_feedback` called, `category="lesson"` |
| `test_platform_feedback` | "App is slow" | `submit_feedback` called, `category="platform"` |
| `test_skip_feedback` | "No thanks" | `skip_feedback` called |
| `test_rating_extracted` | "5 stars" | `rating=5` |
| `test_no_rating_defaults_zero` | "The lesson was well structured and easy to follow" | `rating=0` |

### E2E Smoke Test

```bash
docker compose exec backend python scripts/test_feedback_e2e.py
```

Flow:
1. Create graph with local DynamoDB checkpointer
2. Invoke with "handwriting lesson for letter B, kindergarten"
3. Invoke with "Looks good" → triggers finalize + feedback prompt
4. Invoke with "Great lesson, 5 stars" → feedback collected
5. Query DynamoDB directly → verify feedback record exists with correct `thread_id`
6. Print pass/fail

### Done When

- [x] FeedbackService unit tests pass (4/4)
- [x] Feedback collector node evals pass (5/5)
- [x] E2E smoke test passes (feedback record found in DynamoDB)
- [x] `init_db.py` validates feedback support on startup

---

## Spec Revisions

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-02-10 | Initial draft |
| 0.2 | 2026-02-11 | Implementation complete — all 13 components done, all tests passing |
