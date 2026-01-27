# Architecture v2: Agent-Based Lesson Generator

## Overview

Agent-based architecture using LangGraph's `create_agent` for conversational flexibility with deterministic nodes for consistent lesson generation.

**Status:** In Progress (Phase 3 Complete)

---

## Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                     ROUTING LAYER                                  │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Greeting & Routing Agent                         │  │
│  │                                                               │  │
│  │  - create_agent (langchain.agents) — LangGraph 1.0+          │  │
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
│                 PARAM COLLECTION LAYER                             │
│                                                                    │
│  ┌──────────────────────────────────────────────────────────────┐  │
│  │              Parameter Agent (single agent)                   │  │
│  │                                                               │  │
│  │  - create_agent (langchain.agents) — LangGraph 1.0+          │  │
│  │  - Model: gpt-4o                                             │  │
│  │  - Prompt: Generic (looks at context to pick tool)           │  │
│  │  - Tools: submit_handwriting_params,                         │  │
│  │           submit_vocabulary_params,                          │  │
│  │           submit_idea_generation_params                      │  │
│  └──────────────────────────────────────────────────────────────┘  │
│                                                                    │
│  Extracts task-specific params via tool calls:                     │
│  - Handwriting: grade, letter, student_level                       │
│  - Vocabulary: grade, writing_type, key_vocabulary, objectives     │
│  - Idea Gen: grade, genre, genre_component, writing_stage, obj.    │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
                              │
                              │ params stored in state
                              ▼
┌────────────────────────────────────────────────────────────────────┐
│                    GENERATION LAYER                                │
│                 (Deterministic Nodes)                              │
│                                                                    │
│  ┌──────────────┬───────────────┬───────────────┐                  │
│  │ Handwriting  │  Vocabulary   │     Idea      │                  │
│  │  Generator   │  Generator    │   Generator   │                  │
│  │     ✅       │  (planned)    │   (planned)   │                  │
│  └──────────────┴───────────────┴───────────────┘                  │
│                                                                    │
└────────────────────────────────────────────────────────────────────┘
```

---

## Key Design Decisions

### Routing Agent

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Framework | `create_agent` (LangGraph 1.0+) | Prebuilt, handles agent loop |
| Model | `gpt-4o-mini` | Cost-effective for routing (~20x cheaper than gpt-4o) |
| Tool params | None | Param agent extracts params, not routing agent |
| Prompts | Langfuse | Change without deploy, track versions, A/B test |
| Greeting | Static (not agent-generated) | Avoids double-greeting bug on session init |

### Param Agent

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Architecture | Single agent for all task types | Less duplication, easier to add tasks |
| Framework | `create_agent` (LangGraph 1.0+) | Same pattern as routing |
| Model | `gpt-4o` | Better instruction following for extraction |
| Tools | Task-specific (one tool per task type) | Explicit handoff, structured extraction |
| Prompt | Generic (context-aware) | No prompt changes needed for new task types |
| State storage | TypedDict per task type | Type-safe, clear generator contracts |
| Tool validation | Pydantic | Validates LLM args at boundary |

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

### Handwriting ✅ Implemented

| Parameter | Type | Required |
|-----------|------|----------|
| grade | `Literal["PreK", "K", "1st"]` | Yes |
| letter | `str` | Yes |
| student_level | `Literal["struggling", "on-level", "advanced"]` | No |

### Vocabulary ✅ Implemented

| Parameter | Type | Required |
|-----------|------|----------|
| grade | `Literal["PreK", "K", "1st"]` | Yes |
| writing_type | `Literal["informational", "narrative", "personal_narrative", "opinion"]` | Yes |
| key_vocabulary | `list[str]` | Yes |
| objectives | `str` | Yes |
| student_level | `Literal["struggling", "on-level", "advanced"]` | No |

### Idea Generation ✅ Implemented

| Parameter | Type | Required |
|-----------|------|----------|
| grade | `Literal["PreK", "K", "1st"]` | Yes |
| genre | `Literal["narrative", "informational", "opinion"]` | Yes |
| genre_component | `str` | Yes |
| writing_stage | `Literal["brainstorm", "initial_draft", "revise", "edit"]` | Yes |
| objectives | `str` | Yes |
| student_level | `Literal["struggling", "on-level", "advanced"]` | No |

---

## Evaluation Strategy

### Per-Layer Evals

| Layer | Criteria | Target |
|-------|----------|--------|
| Routing | `routing_accuracy` | >= 90% |
| Routing | `turn_efficiency` | <= 2.0 avg turns |
| Param Agent (Handwriting) | `param_extraction_accuracy` | >= 85% |
| Param Agent (Vocabulary) | `vocab_param_extraction_accuracy` | >= 85% |
| Param Agent (Idea Gen) | `idea_param_extraction_accuracy` | >= 60% |
| Generation | `structure_complete` | >= 80% |
| Generation | `verbatim_check` | >= 60% (word overlap) |
| Generation | `verbal_cues_correct` | >= 75% |

### Eval Workflow

1. Define test cases in `tests/datasets/<layer>.py`
2. Sync to Langfuse dataset
3. Run experiment with run name (e.g., `v1-gpt4o-mini`)
4. View results in Langfuse dashboard
5. Iterate until thresholds met

---

## Implementation Roadmap

Incremental approach — each phase is a separate spec with its own evals.

### Phase 1: Routing Agent ✅ Implemented

**Spec:** `010-routing-agent`

- ReAct agent for greeting + routing
- Three routing tools (no params)
- Placeholder nodes for task agents
- Prompts in Langfuse (`routing-agent` prompt)
- Static greeting on init
- Evals: `routing_accuracy` >= 90%, `turn_efficiency` <= 2.0

---

### Phase 2: Parameter Agent ✅ Implemented

**Spec:** `011-param-agent`

- Single ReAct agent for all task types
- Handwriting tool implemented (`submit_handwriting_params`)
- Generic prompt (context-aware, no changes for new tools)
- Node wrapper extracts tool args into state
- Evals: `param_extraction_accuracy` >= 85%

---

### Phase 3: Handwriting Generator ✅ Implemented

**Spec:** `013-handwriting-generator`

- ReAct agent with `finalize_lesson` tool for multi-turn modifications
- Uses Forms B, C, D, F, H reference materials
- Conditional entry routing for modification loop
- Evals: `structure_complete` >= 80%, `verbatim_check` >= 60%, `verbal_cues_correct` >= 75%
- Test results: 91% pass rate (10/11 tests)

---

### Phase 4: Vocabulary & Idea Generation ✅ Implemented

**Spec:** `012-vocab-idea-params`

- Added `submit_vocabulary_params` and `submit_idea_generation_params` tools
- Added `VocabularySyntaxParams` and `IdeaGenerationParams` state fields
- Added generator placeholders for both task types
- Updated routing to send vocab/idea_generation to param agent
- Evals: `vocab_param_extraction_accuracy` >= 85%, `idea_param_extraction_accuracy` >= 60%

---

### Phase 5: Quality Evals

**Spec:** `014-quality-evals` (planned)

- LLM-as-judge criteria
- `activity_appropriate`, `objective_alignment`
- Track scores over time

---

## Current Implementation Files

### Routing Layer (Phase 1)

| File | Purpose |
|------|---------|
| `app/graph/agents/routing.py` | Routing agent + tools |
| `tests/datasets/routing_agent.py` | Routing eval test cases |
| `tests/evals/test_routing_agent.py` | Routing eval tests |

### Param Collection Layer (Phase 2 + 4)

| File | Purpose |
|------|---------|
| `app/graph/agents/param.py` | Param agent + all three tools |
| `app/graph/state.py` | GraphState with all param TypedDicts |
| `tests/datasets/param_agent.py` | Handwriting param test cases |
| `tests/datasets/vocab_params.py` | Vocabulary param test cases |
| `tests/datasets/idea_params.py` | Idea generation param test cases |
| `tests/evals/test_param_agent.py` | Handwriting param eval tests |
| `tests/evals/test_vocab_params.py` | Vocabulary param eval tests |
| `tests/evals/test_idea_params.py` | Idea generation param eval tests |

### Generation Layer (Phase 3)

| File | Purpose |
|------|---------|
| `app/graph/agents/handwriting_generator.py` | Handwriting generator agent + finalize tool |
| `prompt/reference_materials/handwriting_reference.md` | L4C Forms B, C, D, F, H |
| `tests/datasets/handwriting_generator.py` | Generator test cases (14) |
| `tests/evals/test_handwriting_generator.py` | Generator eval tests |

### Core Infrastructure

| File | Purpose |
|------|---------|
| `app/graph/graph.py` | Graph definition with all nodes and routing |
| `app/graph/nodes/placeholders.py` | Generator placeholders |
| `app/langfuse/criteria.py` | Evaluation criteria |
| `app/langfuse/service.py` | Langfuse helper functions |
| `app/llm/client.py` | Model registry access |
| `scripts/setup_prompts.py` | Langfuse prompt setup |

---

## Open Questions

1. Should agents remember user preferences across sessions?
2. How to handle very long conversations (context window limits)?
3. Where does human review fit in the generation pipeline?
4. How to handle user changing mind mid-collection? (e.g., "actually I want vocabulary")

---

## Spec Revisions

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-01-13 | Initial proposal |
| 0.2 | 2026-01-23 | Updated based on 010 spec discussion: ReAct agent, Langfuse prompts, eval strategy |
| 0.3 | 2026-01-24 | Sync with 010 implementation: LangGraph 1.0 API, static greeting, 90% accuracy target |
| 0.4 | 2026-01-25 | Phase 2 complete: Single param agent, 85% accuracy target, removed v1 references |
| 0.5 | 2026-01-26 | Phase 4 complete: Vocab and idea generation param tools, updated task parameters |
| 0.6 | 2026-01-26 | Phase 3 complete: Handwriting generator with modification loop, 91% test pass rate |
