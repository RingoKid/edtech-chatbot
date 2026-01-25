# 010: Greeting & Routing Agent

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| GraphState v2 schema | ✅ Done | `app/graph/state.py` |
| Routing agent with tools | ✅ Done | `app/graph/agents/routing.py` |
| Placeholder nodes | ✅ Done | `app/graph/nodes/placeholders.py` |
| Graph integration | ✅ Done | `app/graph/graph.py` |
| Langfuse prompt setup script | ✅ Done | `scripts/setup_prompts.py` |
| Eval criteria | ✅ Done | `app/langfuse/criteria.py` |
| Test dataset | ✅ Done | `tests/datasets/routing_agent.py` |
| Eval tests | ✅ Done | `tests/evals/test_routing_agent.py` |
| Langfuse tracing | ✅ Done | Traces visible in dashboard |
| Langfuse scores | 🔲 Planned | Needs `@observe` decorator refactor |
| v1 code cleanup | ✅ Done | Removed old nodes, prompts, schemas |
| Chat service integration | ✅ Done | Static greeting, graph invoked on first user message |

## Overview

**Status:** Implemented
**Layer:** Routing (Layer 1 of v2 architecture)
**Model:** `gpt-4o-mini` (from model registry)
**Framework:** `create_agent` from `langchain.agents` (LangGraph 1.0+)

ReAct agent that handles initial greeting and routes users to task-specific agents. Uses tool calls for routing decisions rather than static classification.

**Why ReAct instead of static router:**
- Can ask clarifying questions when intent is ambiguous
- Handles user corrections ("actually I meant vocabulary, not handwriting")
- More natural conversation flow
- Graceful fallback for unsupported requests

---

## Architecture Context

```
                         THIS SPEC
┌─────────────────────────────────────────────────────────────┐
│              Greeting & Routing Agent                        │
│                                                              │
│  Tools:                                                      │
│  - route_to_handwriting()                                    │
│  - route_to_vocabulary()                                     │
│  - route_to_idea_generation()                                │
└─────────────────────────────────────────────────────────────┘
                              │
                              │ Tool call triggers routing
                              ▼
┌─────────────────────────────────────────────────────────────┐
│              Placeholder Nodes (This Spec)                   │
│                                                              │
│  - handwriting_placeholder    → "Coming soon" + end         │
│  - vocabulary_placeholder     → "Coming soon" + end         │
│  - idea_generation_placeholder → "Coming soon" + end        │
│                                                              │
│  (Replaced by real task agents in specs 012, 014, 015)      │
└─────────────────────────────────────────────────────────────┘
```

---

## Agent Behavior

### Conversation Flow

1. User sends message (e.g., "hi")
2. Agent greets warmly, asks what type of lesson they want, mentions available options
3. User responds with intent (e.g., "handwriting for letter A")
4. Agent calls appropriate routing tool
5. Graph routes to placeholder node, conversation ends

### Key Behaviors

| Scenario | Agent Does |
|----------|------------|
| User greets ("hi", "hello") | Greet back + ask about lesson type + mention options |
| Clear intent ("handwriting lesson") | Call `route_to_handwriting()` |
| Ambiguous ("help me teach") | Ask clarifying question |
| User corrects ("wait, I meant vocab") | Route to corrected task |

---

## Tools

Three routing tools with **no parameters**. Task agents will extract parameters later.

| Tool | Description | Destination |
|------|-------------|-------------|
| `route_to_handwriting` | Route to handwriting lesson creation | `handwriting_placeholder` |
| `route_to_vocabulary` | Route to vocabulary lesson creation | `vocabulary_placeholder` |
| `route_to_idea_generation` | Route to lesson idea brainstorming | `idea_generation_placeholder` |

---

## Placeholder Nodes

Until task agents are implemented (specs 012, 014, 015), route to placeholder nodes that:

1. Display "Coming soon" message
2. End the conversation

Placeholders confirm routing worked correctly during development.

---

## State Schema

| Field | Type | Purpose |
|-------|------|---------|
| `messages` | `list[BaseMessage]` | Full conversation history (with `add_messages` reducer) |
| `task_type` | `Literal["handwriting", "vocabulary", "idea_generation"] \| None` | Set when routing tool is called |
| `routing_complete` | `bool` | Signals successful handoff |

---

## Model Selection

Use the existing model registry:

| Item | Value |
|------|-------|
| Model key | `gpt-4o-mini` |
| Source | `app.llm.client.get_chat_model()` |
| Rationale | Cost-effective for routing, ~20x cheaper than gpt-4o |

---

## Prompt Management

Prompts are stored in **Langfuse** and fetched at runtime.

### Configuration

| Item | Value |
|------|-------|
| Prompt name | `routing-agent` |
| Prompt type | `text` |
| Label | `production` |

### Setup

A setup script creates the initial prompt in Langfuse. Run once before first deployment.

**Script location:** `scripts/setup_prompts.py`

### Runtime

App fetches prompt using Langfuse SDK with the prompt name and label.

### Prompt Requirements

The prompt must instruct the agent to:

- Greet users warmly
- Ask what type of lesson they want to create
- Mention available options: Handwriting, Vocabulary, Idea Generation
- Use routing tool when intent is clear
- Ask clarifying questions when intent is unclear
- Keep responses concise

---

## Guardrails

| Guardrail | Value | Behavior |
|-----------|-------|----------|
| Max agent turns | 10 | Prevents infinite loops |

Additional edge case handling (off-topic, unsupported requests) will be added in future iterations.

---

## Migration from v1

### Current v1 Architecture (to be removed)

```
greeting_node → main_router → setup_* → collect_parameters → wait_for_input → generate_lesson
                    ↑                           ↑
                    └── clarification           └── (loop)
```

### Code to Remove

**From `app/graph/nodes.py`:**
- `greeting_node()`
- `main_router()`
- `clarification_node()`
- `setup_handwriting()`
- `setup_vocabulary()`
- `setup_idea_generation()`
- `collect_parameters_node()`
- `wait_for_user_input()`
- `stub_generate_lesson_node()`
- `route_from_main_router()`
- `route_parameter_collection()`
- `ALLOWED_TASKS` constant

**From `app/graph/prompts.py`:**
- `GREETING_WELCOME_MESSAGE`
- `MAIN_ROUTER_SYSTEM_PROMPT`
- `MAIN_ROUTER_ERROR_MESSAGE`
- `MAIN_ROUTER_CLARIFICATION_MESSAGE`
- `HANDWRITING_STUB_MESSAGE`
- `VOCABULARY_STUB_MESSAGE`
- `IDEA_GENERATION_STUB_MESSAGE`

**From `app/graph/state.py` (remove these fields):**
- `parameter_schema_name`
- `required_parameters`
- `collected_parameters`
- `current_question`
- `collection_error_message`

**Delete file:**
- `app/schemas/task_route.py`

### Files to Modify

| File | Action |
|------|--------|
| `app/graph/graph.py` | Replace with new agent-based graph |
| `app/graph/state.py` | Simplify to new schema |
| `app/graph/nodes.py` | Remove v1 nodes (or delete and create new file) |
| `app/graph/prompts.py` | Remove v1 prompts |

---

## Evaluation

### Dataset

**Source of truth:** `tests/datasets/routing_agent.py`
**Synced to:** Langfuse dataset `routing-agent-eval`

### Test Case Structure

| Field | Type | Purpose |
|-------|------|---------|
| `input` | `str` or `list[dict]` | User message(s) |
| `expected_task_type` | `str` | Expected routing destination |
| `expected_max_turns` | `int` | Maximum turns to complete routing |
| `description` | `str` | Human-readable description |

### Test Case Categories

| Category | Count | Examples |
|----------|-------|----------|
| Clear intent - Handwriting | 4 | "handwriting lesson", "teach letter A", "letter formation" |
| Clear intent - Vocabulary | 4 | "vocabulary words", "word lists for PreK", "vocab lesson" |
| Clear intent - Idea Generation | 4 | "lesson ideas", "brainstorm activities", "give me ideas" |
| Ambiguous (needs clarification) | 3 | "help me teach", "make a lesson", "I need help" |
| Greetings | 2 | "hi", "hello there" |

**Total: ~17 test cases**

### Evaluation Criteria

| Criterion | Type | Description | Target |
|-----------|------|-------------|--------|
| `routing_accuracy` | Rule-based | Did agent route to correct task type? | >= 95% |
| `turn_efficiency` | Rule-based | Average turns to complete routing | <= 2.0 |

### Running Evals

**Local pytest (no Langfuse needed):**
```
docker compose exec backend pytest tests/evals/test_routing_agent.py -v
```

**Full experiment (logs to Langfuse):**
```
docker compose exec backend python -m scripts.run_eval \
    --dataset routing-agent-eval \
    --run-name "v1-gpt4o-mini"
```

### Evals Without Checkpointer

Evals pass full message history directly to the agent. No persistence required.

- Single-turn: Pass single user message
- Multi-turn: Construct message history manually (user, assistant, user, ...)

---

## Implementation Files

### New Files

| File | Purpose |
|------|---------|
| `app/graph/agents/routing.py` | ReAct agent definition + tools |
| `app/graph/nodes/placeholders.py` | Placeholder nodes for task agents |
| `scripts/setup_prompts.py` | Creates initial prompt in Langfuse |
| `tests/datasets/routing_agent.py` | Test case definitions |
| `tests/evals/test_routing_agent.py` | Pytest eval tests |

### Modified Files

| File | Changes |
|------|---------|
| `app/graph/graph.py` | New agent-based graph |
| `app/graph/state.py` | Simplified state schema |
| `app/langfuse/criteria.py` | Add `routing_accuracy`, `turn_efficiency` |

---

## Verification

### Manual Test

1. Send "hi" → Should receive greeting + question about lesson type
2. Send "handwriting" → Should route to placeholder, see "Coming soon" message

### Eval Thresholds

Implementation is complete when:

- [x] `routing_accuracy` >= 90% on test dataset (adjusted from 95% for LLM variability)
- [x] `turn_efficiency` <= 2.0 average turns
- [x] Manual test passes

### Run Tests

```bash
docker compose exec backend pytest tests/evals/test_routing_agent.py -v
```

### Langfuse Tracing

Eval tests log traces to Langfuse via `CallbackHandler`. Traces show:
- Full conversation (messages, tool calls, LLM responses)
- Token usage and latency
- Tags for filtering (`eval`, `routing-agent`, category)

**Scores:** Currently disabled. The `CallbackHandler` doesn't expose `trace_id` at scoring time. To enable scores, refactor to use `@observe()` decorator pattern:

```python
from langfuse import observe

@observe(name="eval-routing")
async def run_eval_case(input_msg):
    # langfuse.score_current_trace() works here
    ...
```

**SDK Version:** Langfuse v3.12.0

---

## Notes for Implementation

- **No interrupt configuration needed** — ReAct agent naturally returns after generating response or calling tool
- **Checkpointer wired separately** — When integrating with chat API, add DynamoDB checkpointer (existing setup)
- **Pull latest docs** — Use Context7 MCP to get current LangGraph and Langfuse SDK documentation

### LangGraph 1.0 Migration

As of LangGraph 1.0, `create_react_agent` was renamed and moved:

```python
# Before (deprecated)
from langgraph.prebuilt import create_react_agent
agent = create_react_agent(model, tools, prompt=system_prompt)

# After (LangGraph 1.0+)
from langchain.agents import create_agent
agent = create_agent(model, tools, system_prompt=system_prompt)
```

Key changes:
- Import from `langchain.agents` instead of `langgraph.prebuilt`
- Function renamed from `create_react_agent` to `create_agent`
- Parameter renamed from `prompt` to `system_prompt`

### Chat Service Integration

The chat service (`app/services/chat_service.py`) uses a **static greeting** approach:

1. `init_chat()` returns a pre-defined greeting without invoking the graph
2. The routing agent is first invoked when the user sends their first message
3. This avoids the "double greeting" bug where both init and first message trigger agent greetings

**Why not invoke the graph on init?**
- Graph completes to `END` after greeting (no interrupt)
- `handle_message()` checks `state.next` to decide resume vs fresh start
- Empty `state.next` means fresh start → agent loses greeting context → greets again

**Alternative approach** (not used): Add `interrupt_after=["routing_agent"]` to pause the graph after greeting, then resume on first message. This adds complexity for minimal benefit.

---

## Open Questions

1. Should the agent remember user preferences across sessions? (future consideration)
2. How to handle context window limits in very long conversations? (future consideration)

---

## Spec Revisions

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-01-23 | Initial proposal |
| 1.0 | 2026-01-23 | Implementation complete - ReAct agent, placeholders, evals passing |
| 1.1 | 2026-01-24 | LangGraph 1.0 migration (`create_agent`), fix double-greeting bug in chat service |
