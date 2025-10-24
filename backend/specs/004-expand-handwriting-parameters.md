-----

### FEATURE SPEC: 000 - Project Common

*(Included for context - see original file for full content)*

  * **Core Architectural Principles:** LangGraph, Unified State, Pydantic Tool Routing, `interrupt_after` Pausing.
  * **Execution Environment:** All commands via `docker compose exec backend ...`
  * **Workflow:** Implement -\> Rebuild (`docker compose down && docker compose up -d --build`) -\> Test (`docker compose exec backend pytest ...`) -\> Fix -\> Sync Spec.

-----

### FEATURE SPEC: 004 - Expand Handwriting Parameters

**Reference:** This builds upon `FEATURE SPEC: 000 - Project Common`, `FEATURE SPEC: 001 - Greeting & Main Router`, `FEATURE SPEC: 002 - Main Router Clarification Loop`, and `FEATURE SPEC: 003 - Dynamic Parameter Collection`. Assumes Docker execution environment as defined in `000`.

**Objective:** Add task-specific parameters (`query_type` and `target_letters`) to the `HandwritingParams` Pydantic schema. Verify that the existing dynamic parameter collection logic correctly handles these additions by asking the appropriate questions in sequence.

#### 1\. File: `app/schemas/lesson_params.py`

**Action:** Modify the `HandwritingParams` Pydantic model to include the new fields.

**Content:**

```python
# [Modify Schema]
from pydantic import BaseModel, Field
from typing import Literal

class BaseLessonParams(BaseModel):
    """Base parameters common to most lesson plans."""
    target_grade: Literal["Pre-K", "Kindergarten", "First Grade", "__CLARIFY__"] = Field(
        ...,
        description="What is the target grade level for this lesson?"
    )

class HandwritingParams(BaseLessonParams):
    """Parameters specific to handwriting lessons."""
    query_type: Literal[
        "letter_formation",
        "fine_motor",
        "spelling",
        "assessment",
        "general",
        "__CLARIFY__"
    ] = Field(
        ...,
        description="Which specific aspect of handwriting do you want to focus on for this lesson?"
    )
    target_letters: str = Field(
        ...,
        description="Which specific letter(s) do you want to focus on for this lesson? (e.g., 'a', 'b, c', or 'None')"
    )
    # Add other handwriting-specific fields here later

# ... (VocabularyParams and IdeaGenerationParams remain unchanged for now) ...

class VocabularyParams(BaseLessonParams):
    """Parameters specific to vocabulary lessons."""
    pass

class IdeaGenerationParams(BaseLessonParams):
    """Parameters specific to idea generation lessons."""
    pass
```

  * **Rationale:** Adds the `query_type` (with `Literal` options and `__CLARIFY__`) and `target_letters` (as `str`) fields specifically to the `HandwritingParams` schema. The `collect_parameters_node` from Spec 003 is expected to handle these additions automatically.

#### 2\. File: `app/graph/state.py`

**Action:** No changes required. The existing `GraphState` fields (`parameter_schema_name`, `required_parameters`, `collected_parameters`, `current_question`, `collection_error_message`) are sufficient.

#### 3\. File: `app/graph/nodes.py`

**Action:** No changes required.

  * The `setup_handwriting` node will automatically detect the new fields when inspecting `HandwritingParams.model_fields.keys()`.
  * The `collect_parameters_node` is designed to dynamically handle any fields listed in `required_parameters`, generate questions from descriptions, handle `Literal` types, and perform extraction using dynamic single-field models.

#### 4\. File: `app/graph/graph.py`

**Action:** No changes required. The existing graph structure and edges for the parameter collection loop remain the same.

#### 5\. File: `app/service/chat_service.py`

**Action:** No changes required. The chat service's resumption logic is agnostic to the specific parameters being collected.

#### 6\. Unit Tests

**File:** `tests/test_parameter_collection.py`

  * **Modify Existing Tests:**
      * Update tests (like `test_collect_single_parameter_success`) to reflect the new sequence for Handwriting:
        1.  User selects "Handwriting".
        2.  AI asks for `target_grade`.
        3.  User provides valid grade.
        4.  AI asks for `query_type` (with options).
        5.  User provides valid query type.
        6.  AI asks for `target_letters`.
        7.  User provides target letters.
        8.  Verify final state: `required_parameters` is empty, `collected_parameters` contains all three values (`target_grade`, `query_type`, `target_letters`).
        9.  Verify final AI message is the stub generation message.
  * **Add New Tests:**
      * **`test_collect_handwriting_query_type_invalid`**:
        1.  Start Handwriting, provide valid `target_grade`.
        2.  AI asks for `query_type`.
        3.  User provides an invalid choice (e.g., "cursive").
        4.  Verify AI responds with the error message ("Sorry, I didn't quite understand...") AND re-asks the `query_type` question with options.
        5.  Verify state: `required_parameters == ["query_type", "target_letters"]`, `collected_parameters` only contains `target_grade`.
      * **`test_collect_handwriting_query_type_clarify`**:
        1.  Start Handwriting, provide valid `target_grade`.
        2.  AI asks for `query_type`.
        3.  User provides an ambiguous response (e.g., "help with writing").
        4.  Verify AI responds with the error message ("Sorry, I didn't quite understand...") AND re-asks the `query_type` question with options (because the extractor LLM should return `__CLARIFY__`).
        5.  Verify state is the same as in `test_collect_handwriting_query_type_invalid`.
      * **`test_collect_handwriting_target_letters_success`**: Ensure simple string extraction works after a valid `query_type` is provided.
      * **`test_collect_handwriting_full_flow_invalid_then_valid`**: Combine scenarios, e.g., invalid `query_type` -\> re-ask -\> valid `query_type` -\> ask `target_letters` -\> valid `target_letters` -\> success.

**Run tests:**

```bash
docker compose exec backend pytest tests/test_parameter_collection.py -v
```

*(Refer to `FEATURE SPEC: 000` for full Docker execution workflow)*

#### 7\. LangSmith Evaluation Strategy

  * **Dataset:** "Feature 4: Parameter Collection - Handwriting" (or update "Feature 3")
  * **Examples:** Create multi-turn examples demonstrating the full collection flow for Handwriting, including cases with valid, invalid, and unclear inputs for `query_type`.
      * *Example 1 (Success):* User: "Handwriting" -\> AI: (Grade Q) -\> User: "Kindergarten" -\> AI: (Query Type Q) -\> User: "letter formation" -\> AI: (Target Letters Q) -\> User: "a, b, c" -\> AI: (Stub Generate Msg)
      * *Example 2 (Clarify Query Type):* User: "Handwriting" -\> AI: (Grade Q) -\> User: "Pre-K" -\> AI: (Query Type Q) -\> User: "making shapes" -\> AI: (Error + Query Type Q again) -\> User: "fine\_motor" -\> AI: (Target Letters Q) -\> User: "None" -\> AI: (Stub Generate Msg)
  * **Evaluators:**
    1.  **"Parameter Collection Sequence" (Custom Code/JSON):** Verify that the questions for `target_grade`, `query_type`, and `target_letters` are asked in the correct order. Check `state.current_question` after each AI turn.
    2.  **"Query Type Options Presented" (Regex/String Match):** Check that the AI message asking for `query_type` includes the `Literal` options (excluding `__CLARIFY__`).
    3.  **"Parameter Extraction Correctness" (Custom Code/JSON):** Check `state.collected_parameters` after each valid user response to ensure the correct value was extracted and added. Verify `state.required_parameters` is updated correctly.
    4.  **"Query Type Clarification Handling" (Custom Code/JSON + Regex):** After invalid/unclear input for `query_type`, check that `state.collection_error_message` is set, the AI response includes the error, and `state.current_question` is still the `query_type` question.

-----