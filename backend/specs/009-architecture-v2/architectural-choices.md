# Architectural Choices for Chatbot Design

Reference of patterns and trade-offs for designing the lesson generator chatbot.

---

## 1. Overall Architecture Patterns

### State Machine (Current v1)

```
greeting → router → {task_a | task_b | task_c}
              ↑              │
              └── clarify ←──┘
```

| Pros | Cons |
|------|------|
| Predictable flow | Rigid — new paths require code changes |
| Easy to debug/trace | Less natural conversation |
| Deterministic once classified | Can feel "scripted" to users |
| Lower cost (fewer LLM calls) | |

**Best for:** Structured tasks, compliance-heavy flows, predictable UX

### ReAct Agent

```
User input → LLM reasons → Calls tool → Observes → Repeats
```

| Pros | Cons |
|------|------|
| Flexible — adapts to conversation | Less predictable |
| Natural dialogue | Harder to debug ("why did it do that?") |
| Handles edge cases gracefully | Higher cost (more LLM calls) |
| | Can go off-track without guardrails |

**Best for:** Open-ended tasks, research, complex reasoning

### Hybrid (Proposed v2)

```
Routing (fast) → Task Agent (flexible) → Generator (deterministic)
```

| Pros | Cons |
|------|------|
| Best of both worlds | More complex to implement |
| Flexibility where needed | Multiple patterns to maintain |
| Control where needed | Handoff logic can be tricky |

**Best for:** Production systems needing both flexibility and consistency

---

## 2. Routing Options

### A. Structured Output Classification

```python
class TaskRoute(BaseModel):
    task_name: Literal["Handwriting", "Vocabulary", "Idea Generation"]

llm.with_structured_output(TaskRoute).invoke(user_message)
```

| Pros | Cons |
|------|------|
| Type-safe | Requires LLM call |
| Pydantic validation | Limited to predefined options |
| Easy error handling | |

### B. Semantic Router (Embedding-based)

```python
routes = [
    Route(name="handwriting", utterances=["writing letters", "letter formation"]),
    Route(name="vocabulary", utterances=["vocab", "word lists"]),
]
router = SemanticRouter(routes)
router("teach kids to write")  # → "handwriting"
```

| Pros | Cons |
|------|------|
| Fast — no LLM call | Less flexible |
| Cheap | Requires good example utterances |
| Deterministic | May miss nuanced intent |

### C. ReAct Agent Router

```python
routing_agent = Agent(
    tools=[route_to_handwriting, route_to_vocabulary, route_to_idea],
    system_prompt="Determine which lesson type the user wants..."
)
```

| Pros | Cons |
|------|------|
| Can ask clarifying questions | Slower |
| Handles ambiguity naturally | More expensive |
| Conversational | May over-clarify |

---

## 3. Agent Handoff Patterns

### A. Tools ARE Sub-Agents

```python
routing_agent = Agent(tools=[
    handwriting_agent.as_tool(),
    vocabulary_agent.as_tool(),
])
# Routing agent directly calls sub-agent as a tool
```

| Pros | Cons |
|------|------|
| Single agent orchestrates | Nested agent calls |
| Natural "delegation" | Harder to trace |
| | Context passing can be tricky |

### B. Explicit Graph Handoff

```python
def route_to_task(state):
    return state["task_type"]  # Returns edge name

graph.add_conditional_edges("router", route_to_task, {
    "handwriting": "handwriting_agent",
    "vocabulary": "vocabulary_agent",
})
```

| Pros | Cons |
|------|------|
| Clear flow in graph | More boilerplate |
| Easy to visualize | Explicit edges for each path |
| State passed cleanly | |

### C. Supervisor Pattern

```python
supervisor = Agent(
    tools=[delegate_to_agent, take_over, escalate],
    system_prompt="Monitor sub-agent progress..."
)
```

| Pros | Cons |
|------|------|
| Can intervene if stuck | Extra LLM calls |
| Quality control | Complexity |
| Graceful degradation | |

---

## 4. Parameter Collection Patterns

### A. One Node Per Parameter

```
ask_grade → ask_letter → ask_level → generate
```

| Pros | Cons |
|------|------|
| Simple logic per node | Many nodes |
| Clear what's being collected | Rigid order |
| | Doesn't handle "grade K, letter A" in one message |

### B. Dynamic Parameter Loop

```python
def collect_params(state):
    missing = get_missing_params(state)
    if not missing:
        return {"ready": True}
    return {"messages": [ask_for(missing[0])]}
```

| Pros | Cons |
|------|------|
| Flexible order | Still one-at-a-time |
| Single node | |

### C. Agent with Structured Tool

```python
class CollectParams(BaseModel):
    grade: str | None
    letter: str | None
    ready: bool  # Agent decides when complete

agent = Agent(tools=[CollectParams])
# Agent fills the "form" through conversation
```

| Pros | Cons |
|------|------|
| Can extract multiple params at once | Agent may miss params |
| Natural conversation | Need validation |
| Agent decides when "done" | |

---

## 5. Memory Scope Options

### A. No Memory (Stateless)

Each request is independent. State passed in request body.

**Use for:** Generation nodes, stateless APIs

### B. Session Memory

Conversation history within a session (thread_id).

**Use for:** Task agents, parameter collection

### C. Cross-Session Memory

Remember user preferences across conversations.

**Use for:** User settings (preferred grade level, favorite activities)

### D. Shared Knowledge

RAG or knowledge base shared across all users.

**Use for:** Curriculum standards, activity templates

---

## 6. Guardrail Options

### A. Max Turns

```python
if state["turns"] > MAX_TURNS:
    return fallback_or_error()
```

### B. Allowed Actions

```python
ALLOWED_TOOLS = ["collect_params", "ask_clarification"]
# Agent can't call arbitrary tools
```

### C. Output Validation

```python
result = agent.invoke(input)
if not validate_output(result):
    return retry_or_fallback()
```

### D. Supervisor Intervention

Separate agent monitors and can take over.

---

## 7. Evaluation Architecture

### A. Post-Generation Only

```
Generate → Evaluate → Return (with scores)
```

**Current implementation.** Simple but no intermediate checks.

### B. Multi-Point Evaluation

```
Route → eval → Collect Params → eval → Generate → eval
```

Catches issues earlier but more complex.

### C. Human-in-the-Loop

```
Generate → Auto-eval → If low score → Human review → Return
```

Quality gate before delivery.

---

## Decision Matrix

| Decision | Recommended | Rationale |
|----------|-------------|-----------|
| Overall architecture | Hybrid | Flexibility + control |
| Routing | Semantic router (fast) or structured output (simple) | Cost-effective for clear intents |
| Task agents | ReAct with structured tool | Natural param collection |
| Handoff | Explicit graph edges | Clear flow, easy debugging |
| Memory | Session-scoped | Sufficient for task completion |
| Guardrails | Max turns + output validation | Prevent infinite loops |
| Evals | Post-generation (expand later) | Start simple |
