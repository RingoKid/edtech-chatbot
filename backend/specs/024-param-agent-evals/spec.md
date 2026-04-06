# 024: Param Agent — Fix Question Skipping & Multi-Turn Evals

## Problem

The param agent skips asking about `previously_learned` and `skill_focus`. It submits the tool call with guessed/default values after collecting only grade + letter. The teacher never gets asked.

**Root cause (3 layers):**

1. **Pydantic field descriptions** hint at defaults — the LLM reads `"Empty list [] if first lesson"` and `"Use isolating_sounds if teacher has no preference"` and infers it can skip asking.
2. **Extraction fallbacks** in `extract_handwriting_params()` silently fill defaults via `.get('field', default)` — even if the LLM omits a field, extraction covers it up.
3. **System prompt** labels these fields as "Optional" with explicit defaults — tells the agent it's OK to not ask.

Pydantic schema defaults were already removed (commit `b05191f`), but that only ensures the LLM *provides* values — it can still guess them from field descriptions without asking.

## Scope

This spec covers:
- Fix field descriptions and prompt to prevent question skipping
- Remove extraction fallbacks in `graph.py`
- Rewrite param agent evals from scratch with multi-turn support
- Cover all scenarios: complete, partial, drip-feed, invalid

This spec does NOT cover:
- Vocabulary or idea generation param tools (same pattern, future work)
- Langfuse prompt sync (prompt changes are code-only for now)

---

## Changes

### 1. Fix Pydantic field descriptions (`app/graph/agents/param.py:117-135`)

Remove default hints from `SubmitHandwritingParams`. The descriptions must tell the LLM to ask, not what to assume.

**Before:**
```python
previously_learned: list[str] = Field(
    description="Sounds/letters already taught (e.g., ['m', 'a', 's', 't']). Empty list [] if first lesson."
)
skill_focus: Literal["isolating_sounds", "blending", "letter_formation", "spelling"] = Field(
    description="Primary skill to target: isolating_sounds, blending, letter_formation, or spelling. Use isolating_sounds if teacher has no preference."
)
```

**After:**
```python
previously_learned: list[str] = Field(
    description="Sounds/letters the students have already learned. Ask the teacher — do not assume or leave empty."
)
skill_focus: Literal["isolating_sounds", "blending", "letter_formation", "spelling"] = Field(
    description="Primary skill to target. Ask the teacher which skill to focus on — do not pick a default."
)
```

### 2. Fix system prompt (`app/graph/agents/param.py:29-80`)

Two changes in `DEFAULT_PARAM_PROMPT`:

**a) AVAILABLE TOOLS section** — remove "Optional" labels and default hints for `previously_learned` and `skill_focus`:

```
1. submit_handwriting_params: For handwriting/letter formation lessons
   Required: grade (PreK/K/1st), letter (A-Z), previously_learned, skill_focus
   Optional: student_level (defaults to on-level)
```

**b) COLLECTION TIPS** — remove the fallback instruction. Change:

```
If the teacher doesn't know or skips these, use the defaults (empty list, isolating_sounds).
```

To:

```
If the teacher is unsure about previously_learned, ask what letter-sounds they've covered so far. If truly the first lesson, confirm with the teacher before using an empty list. For skill_focus, briefly explain the four options if the teacher isn't sure.
```

**c) Add a new RULE** (after existing Rule 5):

```
6. Do NOT submit handwriting params until you have answers for: grade, letter, previously_learned, and skill_focus. Do not guess or assume values the teacher hasn't provided.
```

### 3. Remove extraction fallbacks (`app/graph/graph.py:162-189`)

Remove `.get()` fallbacks in `extract_handwriting_params()`. If the LLM omits a field, extraction should still work (TypedDict doesn't enforce at runtime) but the field will be missing — downstream code will surface the error instead of silently using a default.

**Before:**
```python
return HandwritingParams(
    grade=args.get('grade'),
    letter=letter,
    student_level=args.get('student_level', 'on-level'),
    previously_learned=previously_learned,
    skill_focus=args.get('skill_focus', 'isolating_sounds'),
)
```

**After:**
```python
return HandwritingParams(
    grade=args.get('grade'),
    letter=letter,
    student_level=args.get('student_level', 'on-level'),  # keep: student_level IS optional
    previously_learned=previously_learned,
    skill_focus=args.get('skill_focus'),
)
```

Notes:
- `student_level` keeps its `'on-level'` default — it is genuinely optional per prompt rules.
- `skill_focus` loses its default — the LLM must provide it explicitly.
- `previously_learned` already falls back to `[]` via the list comprehension on line 178-180 when the key is missing. Change to require the key: if `'previously_learned' not in args`, return `None` (reject the submission).

### 4. Create eval dataset (`tests/datasets/param_agent.py`)

The old dataset and eval files have been deleted. Create from scratch.

Replace all 18 single-message test cases. New dataset structure:

```python
@dataclass
class ParamTestCase:
    messages: list[str]              # ordered user messages (multi-turn)
    expected_params: dict | None     # None = should NOT submit
    expect_submit_after: int | None  # which turn index triggers submission (0-based), None = never
    description: str
    category: str
```

**Categories and cases:**

#### `complete` — all info in one message (submission on turn 0)

| Case | Message | Expected |
|------|---------|----------|
| All 5 explicit | `"PreK letter m, they've learned a s t, focus on blending, struggling"` | grade=PreK, letter=m, student_level=struggling, previously_learned=[a,s,t], skill_focus=blending |
| All with defaults | `"K letter b on-level, first lesson ever, isolating sounds"` | grade=K, letter=b, student_level=on-level, previously_learned=[], skill_focus=isolating_sounds |
| Natural phrasing | `"1st grade, letter i, they know m a s t p, work on spelling please"` | grade=1st, letter=i, previously_learned=[m,a,s,t,p], skill_focus=spelling |

#### `multi_turn` — information spread across turns

| Case | Messages | Submit after |
|------|----------|-------------|
| Grade+letter then rest | `["PreK letter m", "they know a and s", "blending"]` | Turn 2 |
| One at a time | `["kindergarten", "letter b", "they know m a s t", "letter formation"]` | Turn 3 |
| Grade+letter+level then rest | `["K letter b struggling", "learned m a s t", "isolating sounds"]` | Turn 2 |

#### `partial_no_submit` — partial info, should NOT submit

| Case | Message | Assert |
|------|---------|--------|
| Grade + letter only | `"PreK letter m"` | `handwriting_params is None` |
| Grade + letter + level | `"K letter b struggling"` | `handwriting_params is None` |
| Grade only | `"kindergarten"` | `handwriting_params is None` |
| Letter only | `"letter b"` | `handwriting_params is None` |

#### `invalid` — should ask for correction, never submit

| Case | Message | Assert |
|------|---------|--------|
| Invalid grade | `"5th grade letter m"` | `handwriting_params is None` |
| Invalid grade 2 | `"2nd grade letter b"` | `handwriting_params is None` |

### 5. Create eval test file (`tests/evals/test_param_agent.py`)

The old test file has been deleted. Create from scratch. Do not use `evaluate_param_extraction_accuracy` from `app/langfuse/criteria.py` — it only checks 3 fields. Use inline assertions instead.

#### `run_multi_turn_flow()`

Core helper that sends messages one at a time using graph checkpointing:

```python
async def run_multi_turn_flow(
    graph,
    messages: list[str],
    thread_id: str,
) -> list[TurnResult]:
    """
    Run multi-turn param conversation.

    1. Routes to handwriting (retry up to 3x)
    2. Sends each message sequentially on the same thread
    3. Returns list of TurnResult (one per message)
    """
    config = {"configurable": {"thread_id": thread_id}}

    # Route to handwriting first
    # ... (same retry logic as current run_param_agent_flow)

    turns = []
    for msg in messages:
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=msg)]},
            config,
        )
        params = extract_full_params(result.get("handwriting_params"))
        turns.append(TurnResult(message=msg, params=params))

    return turns
```

#### `extract_full_params()`

Replaces `params_to_dict()` — checks all 5 fields:

```python
def extract_full_params(params: HandwritingParams | None) -> dict | None:
    if params is None:
        return None
    return {
        "grade": params.get("grade"),
        "letter": params.get("letter"),
        "student_level": params.get("student_level"),
        "previously_learned": params.get("previously_learned"),
        "skill_focus": params.get("skill_focus"),
    }
```

#### Test classes

```python
class TestCompleteExtraction:
    """All info in one message — should submit immediately with all 5 fields correct."""

class TestMultiTurn:
    """Info spread across turns — should NOT submit until all fields collected."""
    # For each case: assert params is None on all turns except the last

class TestPartialNoSubmit:
    """Partial info only — should ask follow-up, never submit."""
    # Single message, assert handwriting_params is None

class TestInvalid:
    """Invalid input — should reject and ask for correction."""
```

#### Aggregate accuracy test

```python
async def test_overall_accuracy():
    """Run all extraction cases (complete + final turn of multi_turn). Target: >= 85%."""
```

---

## Implementation Notes

### Use Context7 MCP for docs

Use Context7 MCP tools to look up current documentation for:
- **LangGraph** — `ainvoke()`, checkpointer API, state management
- **Pydantic** — `Field()` descriptor behavior, schema generation for tool calling
- **pytest** — `@pytest.mark.asyncio`, `@pytest.mark.parametrize` with dataclasses

### Running the eval

```bash
docker compose exec backend pytest tests/evals/test_param_agent.py -v
```

Each test case invokes the real graph (routing → param agent) with an in-memory checkpointer. Multi-turn cases maintain state across turns via thread ID. Expect ~60s per case due to LLM calls.

### What NOT to change

- `HandwritingParams` TypedDict in `state.py` — no changes needed
- Vocabulary/idea generation tools — out of scope
- `submit_handwriting_params` function signature defaults — these are runtime defaults, not schema-facing
- Langfuse prompt sync — prompt changes are in `DEFAULT_PARAM_PROMPT` only

---

## Acceptance Criteria

1. **No single-message submission with partial info** — `"PreK letter m"` must return `handwriting_params=None`
2. **Multi-turn completes** — drip-feed flow ends with all 5 fields correctly extracted
3. **All 5 fields verified** — `extract_full_params()` checks grade, letter, student_level, previously_learned, skill_focus
4. **Field descriptions have no default hints** — grep `SubmitHandwritingParams` for "default", "empty list", "if not specified" → zero matches
5. **Extraction has no silent fallbacks** — `extract_handwriting_params()` does not provide defaults for `previously_learned` or `skill_focus`
6. **Eval passes** — `pytest tests/evals/test_param_agent.py -v` with >= 85% accuracy on extraction cases

---

## Files Changed

| File | Change |
|------|--------|
| `app/graph/agents/param.py` | Field descriptions, prompt rules, collection tips |
| `app/graph/graph.py` | Remove extraction fallbacks (lines 178-187) |
| `tests/datasets/param_agent.py` | Create from scratch — multi-turn cases (old file deleted) |
| `tests/evals/test_param_agent.py` | Create from scratch — multi-turn flow + 5-field checks (old file deleted) |
