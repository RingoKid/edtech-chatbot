# Architecture v2: Hybrid Agent-Based Lesson Generator

## Overview

Proposed architecture combining ReAct agents for conversational flexibility with deterministic nodes for consistent lesson generation.

**Status:** Proposal
**Current Implementation:** LangGraph state machine (see `backend/specs/002-lesson-graph/`)

---

## Current vs Proposed

| Aspect | Current (v1) | Proposed (v2) |
|--------|--------------|---------------|
| Routing | LLM structured output → fixed paths | Semantic router or ReAct agent |
| Param collection | Explicit nodes per parameter | Task-specific ReAct agents |
| Generation | Not implemented yet | Deterministic nodes with explicit prompts |
| Flexibility | Low — predefined paths | High — agents adapt to conversation |

---

## Proposed Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                     ROUTING LAYER                                  │
│                                                                    │
│  ┌──────────────────┐                                              │
│  │  Semantic Router │  ← Fast, embedding-based                     │
│  │   or ReAct Agent │  ← Or LLM-based for complex routing          │
│  └────────┬─────────┘                                              │
│           │                                                        │
└───────────┼────────────────────────────────────────────────────────┘
            │ handoff (task_type + conversation_summary)
            ▼
┌────────────────────────────────────────────────────────────────────┐
│                 PARAMETER COLLECTION LAYER                         │
│                    (ReAct Agents)                                  │
│                                                                    │
│  ┌──────────────┬───────────────┬───────────────┐                  │
│  │ Handwriting  │  Vocabulary   │     Idea      │                  │
│  │    Agent     │    Agent      │    Agent      │                  │
│  │              │               │               │                  │
│  │ Collects:    │ Collects:     │ Collects:     │                  │
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
│  │              │               │               │                  │
│  │ Forms B,C,   │ Vocab-        │ Idea-         │                  │
│  │ D,F prompts  │ specific      │ specific      │                  │
│  └──────────────┴───────────────┴───────────────┘                  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
          │
          ▼
┌────────────────────────────────────────────────────────────────────┐
│                     EVALUATION LAYER                               │
│                                                                    │
│  ┌─────────────────────────────────────────────────────────────┐   │
│  │ Rule-based: structure_complete, verbatim_check              │   │
│  │ LLM-as-judge: activity_appropriate, objective_alignment     │   │
│  └─────────────────────────────────────────────────────────────┘   │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Task Parameters

### Handwriting

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| grade | `Literal["PreK", "K", "1st"]` | Yes | Grade level |
| letter | `str` | Yes | Target letter (a-z) |
| student_level | `Literal["struggling", "on-level", "advanced"]` | No | Defaults to on-level |

**Generation inputs:** Forms B, C, D, F (see `n8n/workflows/lesson-generator-v02.json`)

### Vocabulary

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| grade | `Literal["PreK", "K", "1st"]` | Yes | Grade level |
| topic | `str` | Yes | Vocabulary topic |
| word_count | `int` | No | Number of words to include |

**Generation inputs:** TBD

### Idea Generation

| Parameter | Type | Required | Notes |
|-----------|------|----------|-------|
| grade | `Literal["PreK", "K", "1st"]` | Yes | Grade level |
| theme | `str` | Yes | Lesson theme |
| constraints | `str` | No | Any specific constraints |

**Generation inputs:** TBD

---

## Handoff State

When transitioning between layers:

```python
class HandoffState(BaseModel):
    task_type: Literal["handwriting", "vocabulary", "idea"]
    collected_params: dict  # {"grade": "PreK", "letter": "A"}
    conversation_summary: str  # For context continuity
    clarification_attempts: int  # Track loops
```

---

## Guardrails

| Guardrail | Value | Behavior |
|-----------|-------|----------|
| Max clarification turns | 3 | Fall back to defaults or escalate |
| Max agent turns | 10 | Force completion or error |
| Cancellation phrases | "never mind", "cancel" | Exit to greeting |

---

## Evaluation Points

| Layer | Eval Type | Criteria |
|-------|-----------|----------|
| Routing | Rule-based | Correct task classification |
| Param Collection | Rule-based | All required params collected |
| Generation | Rule-based | `structure_complete`, `verbatim_check` |
| Generation | LLM-as-judge | `activity_appropriate`, `objective_alignment`, `guided_practice_nuance` |

See `backend/specs/008-langfuse-evals/spec.md` for eval implementation details.

---

## Current Implementation Files

### LangGraph State Machine (v1)

| File | Purpose |
|------|---------|
| `app/graph/state.py` | GraphState TypedDict |
| `app/graph/nodes.py` | Node functions (greeting, main_router, clarification) |
| `app/graph/graph.py` | Graph definition and compilation |
| `app/graph/prompts.py` | System prompts and messages |
| `app/schemas/task_route.py` | Pydantic routing schema |
| `app/service/chat_service.py` | Graph invocation and resumption |
| `app/routers/chat.py` | REST API endpoints |

### Specs

| Spec | Description |
|------|-------------|
| `002-lesson-graph/001-greeting-main-router.md` | Initial routing implementation |
| `002-lesson-graph/002-main-router-clarification-loop.md` | Clarification loop |
| `002-lesson-graph/003-dynamic-parameter-collection.md` | Parameter collection pattern |
| `002-lesson-graph/004-expand-handwriting-parameters.md` | Handwriting-specific params |
| `002-lesson-graph/005-expand-vocab-idea-gen-parameters.md` | Vocab/Idea params |

### Eval System

| File | Purpose |
|------|---------|
| `app/langfuse/criteria.py` | Evaluation criteria (structure_complete) |
| `app/langfuse/service.py` | compare_models(), dataset functions |
| `app/langfuse/router.py` | `/api/v1/evals/*` endpoints |
| `app/llm/runner.py` | `run_prompt()` for model execution |

---

## Implementation Roadmap

Incremental approach — each phase is a separate spec with its own evals.

### Phase 1: Eval Infrastructure

**Goal:** Add dataset-driven evals so we can test routing before building it.

- Add `routing_accuracy` criterion to Langfuse evals
- Create endpoint to run evals against a dataset (not just single prompts)
- Build initial routing test dataset (20-30 cases)

**Eval:** Can run dataset and get accuracy score in Langfuse.

**Spec:** `010-dataset-evals`

---

### Phase 2: Routing Layer

**Goal:** Replace current structured output routing with something that can handle ambiguity better.

- Decide: semantic router vs structured output (keep simple for now)
- Routing returns task type + extracted info from user message
- Wire into existing graph as replacement for current router

**Eval:** `routing_accuracy` ≥ 95% on test dataset.

**Spec:** `011-v2-routing`

---

### Phase 3: Handwriting Agent

**Goal:** Replace fixed parameter nodes with a conversational agent for handwriting.

- Agent collects grade, letter, student level through conversation
- Can extract multiple params from one message
- Hands off to generation when all required params collected

**Eval:** `param_extraction_accuracy` on handwriting test cases.

**Spec:** `012-handwriting-agent`

---

### Phase 4: Handwriting Generator

**Goal:** Deterministic generation node that takes params and produces lesson.

- Takes collected params as input
- Uses existing Forms B, C, D, F prompts from n8n workflow
- Returns structured lesson output

**Eval:** `structure_complete` (existing), add `verbatim_check` for form content.

**Spec:** `013-handwriting-generator`

---

### Phase 5: Vocabulary & Idea Agents

**Goal:** Repeat Phase 3-4 pattern for remaining task types.

- Vocabulary agent + generator
- Idea generation agent + generator

**Eval:** Same pattern — param extraction + structure checks.

**Spec:** `014-vocab-agent`, `015-idea-agent`

---

### Phase 6: Quality Evals

**Goal:** Add LLM-as-judge evals for lesson quality.

- `activity_appropriate` — activities match grade level
- `objective_alignment` — lesson meets stated objectives

**Eval:** Track scores over time in Langfuse.

**Spec:** `016-quality-evals`

---

## Open Questions

1. Should routing agent have access to conversation history across sessions?
2. How to handle mid-conversation task switching ("actually, let's do vocabulary instead")?
3. Should task agents share a common base class/prompt structure?
4. Where does human review fit in the generation pipeline?
