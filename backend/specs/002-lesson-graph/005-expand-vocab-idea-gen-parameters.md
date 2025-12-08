### FEATURE SPEC: 000 - Project Common

*(Included for context - see original file for full content)*

  * **Core Architectural Principles:** LangGraph, Unified State, Pydantic Tool Routing, `interrupt_after` Pausing.
  * **Execution Environment:** All commands via `docker compose exec backend ...`
  * **Workflow:** Implement -\> Rebuild (`docker compose down && docker compose up -d --build`) -\> Test (`docker compose exec backend pytest ...`) -\> Fix -\> Sync Spec.

-----

### FEATURE SPEC: 005 - Expand Vocabulary and Idea Generation Parameters

**Reference:** This builds upon `FEATURE SPEC: 000 - Project Common`, `FEATURE SPEC: 001 - Greeting & Main Router`, `FEATURE SPEC: 002 - Main Router Clarification Loop`, `FEATURE SPEC: 003 - Dynamic Parameter Collection`, and `FEATURE SPEC: 004 - Expand Handwriting Parameters`. Assumes Docker execution environment as defined in `000`.

**Objective:** Add task-specific parameters to the `VocabularyParams` and `IdeaGenerationParams` Pydantic schemas. Verify that the existing dynamic parameter collection logic correctly handles these additions by asking the appropriate questions in sequence for all task types.

#### 1\. File: `app/schemas/lesson_params.py`

**Action:** Modify the `VocabularyParams` and `IdeaGenerationParams` Pydantic models to include their respective new fields.

**Content:**

```python
# [Modify Schemas]
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
        "letter formation",
        "fine motor",
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

class VocabularyParams(BaseLessonParams):
    """Parameters specific to vocabulary lessons."""
    query_type: Literal[
        "sentence structure",
        "vocabulary building",
        "grammar",
        "genre writing",
        "general",
        "__CLARIFY__"
    ] = Field(
        ...,
        description="Which specific aspect of vocabulary or syntax do you want to focus on?"
    )
    target_vocabulary: str = Field(
        ...,
        description="Are there specific vocabulary words or concepts you want to target? (e.g., 'colors', 'action verbs', 'rhyming words', or 'None')"
    )
    target_genre: str = Field(
        ...,
        description="If focusing on genre writing, which genre? (e.g., 'narrative', 'informational', or 'Not applicable')"
    )

class IdeaGenerationParams(BaseLessonParams):
    """Parameters specific to idea generation lessons."""
    query_type: Literal[
        "idea generation",
        "organization",
        "genre elements",
        "brainstorming",
        "general",
        "__CLARIFY__"
    ] = Field(
        ...,
        description="Which specific aspect of idea generation or organization do you want to focus on?"
    )
    target_genre: Literal[
        "narrative",
        "informational",
        "opinion",
        "personal narrative",
        "compare contrast",
        "__CLARIFY__"
    ] = Field(
        ...,
        description="Which writing genre are we planning for?"
    )
    target_topic: str = Field(
        ...,
        description="What is the specific topic for this writing lesson? (e.g., 'My Family', 'Community Helpers', 'Seasons', or 'Student Choice')"
    )

# Schema registry needs to be updated if it's manually defined anywhere.
# If using dynamic lookup (e.g., globals()), ensure these classes are imported where needed.
SCHEMA_REGISTRY = {
    "HandwritingParams": HandwritingParams,
    "VocabularyParams": VocabularyParams,
    "IdeaGenerationParams": IdeaGenerationParams
}
```

  * **Rationale:** Adds the agreed-upon `query_type`, `target_vocabulary`, and `target_genre` fields to `VocabularyParams`. Adds `query_type`, `target_genre` (as `Literal`), and `target_topic` to `IdeaGenerationParams`. Includes `__CLARIFY__` in `Literal` types as needed. Added a `SCHEMA_REGISTRY` definition as the `collect_parameters_node` needs a way to look up the schema class from the name stored in the state. This needs to be defined or imported where `collect_parameters_node` uses it.

#### 2\. File: `app/graph/state.py`

**Action:** No changes required.

#### 3\. File: `app/graph/nodes.py`

**Action:** Ensure `SCHEMA_REGISTRY` (defined in `app/schemas/lesson_params.py` or elsewhere) is imported and used in `collect_parameters_node` to look up the schema class by name.

**Example Snippet (Conceptual - ensure this lookup exists in `collect_parameters_node`):**

```python
# Inside collect_parameters_node logic:
from app.schemas.lesson_params import SCHEMA_REGISTRY # Ensure this import is present

# ... other imports and logic ...

def collect_parameters_node(state: GraphState):
    # ... get state variables ...
    parameter_schema_name = state["parameter_schema_name"]
    schema = SCHEMA_REGISTRY[parameter_schema_name] # Use registry to get the class
    # ... rest of the node logic ...
```

  * **Rationale:** The `setup_vocabulary` and `setup_idea_generation` nodes will automatically detect the new fields. The `collect_parameters_node` will dynamically handle them, provided it can look up the correct Pydantic schema class using the `parameter_schema_name` from the state. Using a registry is a clean way to manage this lookup.

#### 4\. File: `app/graph/graph.py`

**Action:** No changes required.

#### 5\. File: `app/service/chat_service.py`

**Action:** No changes required.

#### 6\. Unit Tests

**Action:** Create a **new test file** named `tests/test_parameter_collection_all_tasks.py`. You may optionally update `tests/test_parameter_collection.py` to focus *only* on Handwriting or remove redundant tests after creating the new file.

  * **File:** `tests/test_parameter_collection_all_tasks.py`
      * **Test Setup:** Use dependency override for `ChatService` as established previously.
      * **Test Cases for Vocabulary:**
          * `test_collect_vocabulary_success`: Full successful flow (Grade -\> Query Type -\> Target Vocab -\> Target Genre). Verify final state and stub message.
          * `test_collect_vocabulary_query_type_invalid`: Test invalid/unclear input for `query_type` -\> Verify re-ask and state.
          * `test_collect_vocabulary_target_genre_handling`: Test input for the string `target_genre`.
          * `test_collect_vocabulary_invalid_then_valid`: Combine invalid `query_type` then valid flow.
      * **Test Cases for Idea Generation:**
          * `test_collect_idea_gen_success`: Full successful flow (Grade -\> Query Type -\> Target Genre -\> Target Topic). Verify final state and stub message.
          * `test_collect_idea_gen_query_type_invalid`: Test invalid/unclear input for `query_type` -\> Verify re-ask and state.
          * `test_collect_idea_gen_target_genre_invalid`: Test invalid/unclear input for `target_genre` (Literal) -\> Verify re-ask and state.
          * `test_collect_idea_gen_invalid_then_valid`: Combine invalid steps then valid flow.

**Run tests:**

```bash
# Run the new specific test file
docker compose exec backend pytest tests/test_parameter_collection_all_tasks.py -v

# Or run all tests in the directory
docker compose exec backend pytest tests/ -v
```

*(Refer to `FEATURE SPEC: 000` for full Docker execution workflow)*

#### 7\. LangSmith Evaluation Strategy

  * **Dataset:** "Feature 5: Parameter Collection - All Tasks" (or update previous dataset)
  * **Examples:** Add multi-turn examples covering the full collection flows for Vocabulary and Idea Generation, mirroring the new unit test cases (success, invalid/unclear inputs for new `query_type` and `target_genre` fields).
  * **Evaluators:** Extend the evaluators defined in Spec 004:
    1.  **"Parameter Collection Sequence" (Update):** Verify correct question order for Vocabulary (4 questions) and Idea Generation (4 questions).
    2.  **"Query Type/Genre Options Presented" (Update):** Check AI messages asking for `query_type` (Vocab, Idea Gen) and `target_genre` (Idea Gen) include the correct `Literal` options.
    3.  **"Parameter Extraction Correctness" (Update):** Check `state.collected_parameters` includes all expected parameters for Vocabulary and Idea Generation upon successful completion.
    4.  **"Clarification Handling" (Update):** Verify error message and re-asking logic works correctly for the new `Literal` fields (`query_type` in Vocab/Idea Gen, `target_genre` in Idea Gen).

-----