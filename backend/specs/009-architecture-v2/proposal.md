# Architecture v2: Agent-Based Lesson Generator

## Overview

Agent-based architecture using LangGraph's `create_react_agent` for conversational flexibility with deterministic nodes for consistent lesson generation.

**Status:** In Progress
**Current Implementation:** LangGraph state machine (see `backend/specs/002-lesson-graph/`)

---

## Current vs Proposed

| Aspect | Current (v1) | Proposed (v2) |
|--------|--------------|---------------|
| Routing | LLM structured output → fixed paths | ReAct agent with routing tools |
| Param collection | Explicit nodes per parameter | Task-specific ReAct agents |
| Generation | Not implemented yet | Deterministic nodes with explicit prompts |
| Prompts | Hardcoded in codebase | Stored in Langfuse, fetched at runtime |
| Flexibility | Low — predefined paths | High — agents adapt to conversation |

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                     ROUTING LAYER                                  │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Greeting & Routing Agent                         │  │
│  │                                                               │  │
│  │  - create_react_agent (langgraph.prebuilt)                   │  │
│  │  - Model: gpt-4o-mini (cost-optimized)                       │  │
│  │  - Prompt: Fetched from Langfuse                             │  │
│  │  - Tools: route_to_handwriting, route_to_vocabulary,         │  │
│  │           route_to_idea_generation (no params)               │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
                              │
                              │ Tool call (task_type only)
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                 TASK AGENTS LAYER                                  │
│                    (ReAct Agents)                                  │
│                                                                    │
│  ┌──────────────┬───────────────┬───────────────┐                  │
│  │ Handwriting  │  Vocabulary   │     Idea      │                  │
│  │    Agent     │    Agent      │    Agent      │                  │
│  │              │               │               │                  │
│  │ Extracts:    │ Extracts:     │ Extracts:     │                  │
│  │ - grade      │ - grade       │ - grade       │                  │
│  │ - letter     │ - topic       │ - theme       │                  │
│  │ - level      │ - word_count  │ - constraints │                  │
│  └──────┬───────┴───────┬───────┴───────┬───────┘                  │
│         │               │               │                          │
└─────────┼───────────────┼───────────────┼──────────────────────────┘
          │ params        │ params        │ params
          ▼               ▼               ▼
┌────────────────────────────────────────────────────────────────────┐
│                    GENERATION LAYER                                │
│                 (Deterministic Nodes)                              │
│                                                                    │
│  ┌──────────────┬───────────────┬───────────────┐                  │
│  │ Handwriting  │  Vocabulary   │     Idea      │                  │
│  │  Generator   │  Generator    │   Generator   │                  │
│  └──────────────┴───────────────┴───────────────┘                  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

### Routing Agent

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Framework | `create_react_agent` | Prebuilt, handles agent loop |
| Model | `gpt-4o-mini` | Cost-effective for routing (~20x cheaper than gpt-4o) |
| Tool params | None | Task agents extract params, not routing agent |
| Prompts | Langfuse | Change without deploy, track versions, A/B test |

### Evals

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Dataset storage | Local file → sync to Langfuse | Version-controlled, viewable in dashboard |
| Per-layer evals | Yes | Test each layer independently |
| Checkpointer for evals | Not required | Pass message history directly |

### Infrastructure

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Model selection | Existing registry (`app/llm/client.py`) | Centralized configuration |
| Checkpointer | Existing DynamoDB setup | Plug-and-play when wiring to chat API |
| Interrupts | Not needed | ReAct agent naturally returns after response/tool call |

---

## Task Parameters

### Handwriting

| Parameter | Type | Required |
|-----------|------|----------|
| grade | `Literal["PreK", "K", "1st"]` | Yes |
| letter | `str` | Yes |
| student_level | `Literal["struggling", "on-level", "advanced"]` | No |

### Vocabulary

| Parameter | Type | Required |
|-----------|------|----------|
| grade | `Literal["PreK", "K", "1st"]` | Yes |
| topic | `str` | Yes |
| word_count | `int` | No |

### Idea Generation

| Parameter | Type | Required |
|-----------|------|----------|
| grade | `Literal["PreK", "K", "1st"]` | Yes |
| theme | `str` | Yes |
| constraints | `str` | No |

---

## Evaluation Strategy

### Per-Layer Evals

| Layer | Criteria | Target |
|-------|----------|--------|
| Routing | `routing_accuracy` | >= 95% |
| Routing | `turn_efficiency` | <= 2.0 avg turns |
| Task Agents | `param_extraction_accuracy` | >= 90% |
| Generation | `structure_complete` | >= 85% |
| Generation | `verbatim_check` | 100% (rule-based) |

### Eval Workflow

1. Define test cases in `tests/datasets/<layer>.py`
2. Sync to Langfuse dataset
3. Run experiment with run name (e.g., `v1-gpt4o-mini`)
4. View results in Langfuse dashboard
5. Iterate until thresholds met

---

## Implementation Roadmap

Incremental approach — each phase is a separate spec with its own evals.

### Phase 1: Routing Agent ✅ Spec Written

**Spec:** `010-routing-agent`

- ReAct agent for greeting + routing
- Three routing tools (no params)
- Placeholder nodes for task agents
- Prompts in Langfuse
- Evals: `routing_accuracy`, `turn_efficiency`

---

### Phase 2: Handwriting Task Agent

**Spec:** `011-handwriting-agent`

- ReAct agent for parameter collection
- Extracts grade, letter, student_level from conversation
- Hands off to generator when complete
- Evals: `param_extraction_accuracy`

---

### Phase 3: Handwriting Generator

**Spec:** `012-handwriting-generator`

- Deterministic node with explicit prompts
- Uses Forms B, C, D, F structure
- Evals: `structure_complete`, `verbatim_check`

---

### Phase 4: Vocabulary & Idea Generation

**Specs:** `013-vocab-agent`, `014-idea-agent`

- Same pattern as handwriting
- Task-specific parameter extraction
- Task-specific generation

---

### Phase 5: Quality Evals

**Spec:** `015-quality-evals`

- LLM-as-judge criteria
- `activity_appropriate`, `objective_alignment`
- Track scores over time

---

## Current Implementation Files

### v1 (To Be Replaced)

| File | Purpose |
|------|---------|
| `app/graph/state.py` | GraphState TypedDict |
| `app/graph/nodes.py` | Node functions |
| `app/graph/graph.py` | Graph definition |
| `app/graph/prompts.py` | Hardcoded prompts |
| `app/schemas/task_route.py` | Pydantic routing schema |

### Eval System (Keep)

| File | Purpose |
|------|---------|
| `app/langfuse/criteria.py` | Evaluation criteria |
| `app/langfuse/service.py` | compare_models(), dataset functions |
| `app/llm/client.py` | Model registry access |

---

## Open Questions

1. Should agents remember user preferences across sessions?
2. How to handle very long conversations (context window limits)?
3. Where does human review fit in the generation pipeline?

---

## Spec Revisions

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-01-13 | Initial proposal |
| 0.2 | 2026-01-23 | Updated based on 010 spec discussion: ReAct agent, Langfuse prompts, eval strategy |
