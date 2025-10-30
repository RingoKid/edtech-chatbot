### FEATURE SPEC: 003 - Dynamic Parameter Collection (Initial - Grade Only)

**Reference:** This builds upon `FEATURE SPEC: 000 - Project Common`, `FEATURE SPEC: 001 - Greeting & Main Router`, and `FEATURE SPEC: 002 - Main Router Clarification Loop`. Assumes Docker execution environment as defined in `000`.

**Objective:** Implement a dynamic parameter collection loop. Introduce task-specific Pydantic schemas using inheritance for common fields. Create `setup_` nodes to initialize state for collection. Implement a reusable `collect_parameters_node` that asks questions based on schema descriptions (including `Literal` options), attempts extraction using dynamically generated single-field models, validates input, and loops until all required parameters (initially, only `target_grade`) are collected.

#### 1\. File: `app/schemas/lesson_params.py` (NEW)

**Action:** Create base and inherited Pydantic models for lesson parameters.

**Content:**

```python
# [New Schemas]
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
    # Add handwriting-specific fields here later
    pass

class VocabularyParams(BaseLessonParams):
    """Parameters specific to vocabulary lessons."""
    # Add vocabulary-specific fields here later
    pass

class IdeaGenerationParams(BaseLessonParams):
    """Parameters specific to idea generation lessons."""
    # Add idea generation-specific fields here later
    pass
```

  * **Rationale:** Establishes the inheritance structure. For now, only the common `target_grade` field is defined. The `"__CLARIFY__"` option allows the LLM to indicate when user input is unclear or invalid, following the same pattern as `TaskRoute`.

#### 2\. File: `app/graph/state.py`

**Action:** Add new fields to `GraphState` for managing parameter collection.

**Content:**

```python
# [Modify Schema]
from typing import TypedDict, Annotated, List, Optional, Type, Dict, Any
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from pydantic import BaseModel # Added import

class GraphState(TypedDict):
    """
    The unified state object for the entire graph.
    """
    messages: Annotated[List[BaseMessage], add_messages]
    task_name: Optional[str] = None # Make Optional for initialization

    # New fields for parameter collection
    parameter_schema_name: Optional[str] = None # Holds the schema class name (e.g., "HandwritingParams")
    required_parameters: List[str] = [] # List of param names still needed
    collected_parameters: Dict[str, Any] = {} # Stores collected {name: value} pairs
    current_question: Optional[str] = None # The question currently asked
    collection_error_message: Optional[str] = None # Temporary error message for re-asking
```

  * **Rationale:** Adds the necessary keys to track the schema, required/collected parameters, the current question, and any validation errors during the loop. `task_name` is made `Optional` as it won't exist at the very start. Note: `parameter_schema_name` stores the string name of the schema class (not the class itself) to avoid TypedDict serialization issues.

#### 3\. File: `app/graph/nodes.py`

**Action:** Replace stub nodes with `setup_` nodes. Create the `collect_parameters_node` and a stub `generate_lesson_node`. Create the `route_parameter_collection` routing function.

**Node: `setup_handwriting` (Replaces `stub_handwriting_node`)**

  * **Dependencies:** `from app.schemas.lesson_params import HandwritingParams`
  * **Logic:**
    1.  Get all field names: `param_names = list(HandwritingParams.model_fields.keys())`
    2.  Return state update dict:
        ```python
        {
            "parameter_schema_name": "HandwritingParams",
            "required_parameters": param_names,
            "collected_parameters": {},
            "current_question": None, # Ensure clean start
            "collection_error_message": None
        }
        ```

**Node: `setup_vocabulary` (Replaces `stub_vocabulary_node`)**

  * **Dependencies:** `from app.schemas.lesson_params import VocabularyParams`
  * **Logic:** (Similar to `setup_handwriting`, but using `VocabularyParams`)

**Node: `setup_idea_generation` (Replaces `stub_idea_generation_node`)**

  * **Dependencies:** `from app.schemas.lesson_params import IdeaGenerationParams`
  * **Logic:** (Similar to `setup_handwriting`, but using `IdeaGenerationParams`)

**Node: `collect_parameters_node` (NEW)**

  * **Dependencies:** `ChatOpenAI`, `AIMessage`, `HumanMessage`, Pydantic (`create_model`, `ValidationError`), `get_origin`, `get_args` from `typing`, `SCHEMA_REGISTRY` for looking up schema classes by name.
  * **Logic:**
    1.  **Get State:** Retrieve `messages`, `parameter_schema_name`, `required_parameters`, `collected_parameters`, `collection_error_message` from the input `state`. Look up the actual schema class using `SCHEMA_REGISTRY[parameter_schema_name]`.
    2.  **Initialize:** `next_question = None`, `ai_message_content = None`, `error_to_show = state.get("collection_error_message")`
    3.  **Check First Entry:** Determine if this is the first time entering collection by checking if `current_question` is None.
    4.  **Attempt Extraction (if not first entry for this param):**
          * If not first entry AND `required_parameters` is *not* empty AND the last message is from the 'user':
              * Get the parameter name we *were* asking about: `param_to_extract = required_parameters[0]`
              * Get its field definition from `schema.model_fields[param_to_extract]`.
              * **Dynamically Create Single-Field Schema:**
                ```python
                SingleFieldModel = create_model(
                    f"Dynamic_{param_to_extract}",
                    __base__=BaseModel,
                    value=(field_definition.annotation, Field(..., description=field_definition.description))
                )
                ```
              * **Bind to LLM:** `extractor_llm = llm.with_structured_output(SingleFieldModel, strict=True)`
              * **Invoke LLM:** Wrap in `try...except`:
                  * `extracted_result = extractor_llm.invoke(user_response)`
                  * **Check for `__CLARIFY__`:**
                      * If `extracted_value == "__CLARIFY__"`: Set `error_to_show = "Sorry, I didn't quite understand that. Could you please try again?"` and do not modify `collected_parameters` or `required_parameters`.
                  * **On Success (valid value):**
                      * `extracted_value = extracted_result.value`
                      * Add to collected: `collected_parameters[param_to_extract] = extracted_value`
                      * Remove from required: `required_parameters = required_parameters[1:]`
                      * Clear any previous error: `error_to_show = None`
                  * **On `ValidationError` or other Exception:**
                      * `error_to_show = "Sorry, I didn't quite understand that. Could you please try again?"`
                      * *Do not modify `collected_parameters` or `required_parameters`.*
    4.  **Determine Next Action:**
          * **If `required_parameters` is now empty:**
              * Set `current_question = None`
              * Clear error: `error_to_show = None`
              * Get the *next* parameter to ask about: `next_param_name = required_parameters[0]`
              * Get its field definition: `field_info = schema.model_fields[next_param_name]`
              * **Generate Question:**
                  * Start with `field_info.description`.
                  * Check if `field_info.annotation` is a `Literal` using `get_origin` and `get_args`.
                  * If yes, filter out `"__CLARIFY__"` from the choices and append: `f" Please choose one of: {', '.join([choice for choice in get_args(field_info.annotation) if choice != '__CLARIFY__'])}."`
                  * Store in `next_question`.
    5.  **Prepare AI Message:**
          * Combine error (if any) and next question:
            `ai_message_content = (f"{error_to_show}\n\n{next_question}" if error_to_show else next_question)`
    6.  **Return State Update:**
          * Return dict with updated `required_parameters`, `collected_parameters`, `current_question=next_question`, `collection_error_message=error_to_show`, and potentially the new `AIMessage` (using the `add_messages` structure `{"messages": [ai_message]}`).

**Node: `stub_generate_lesson_node` (NEW)**

  * **Logic:**
    1.  Get `collected_parameters` from state.
    2.  Format parameters as a string: `param_str = ", ".join([f"{k}: {v}" for k, v in collected_params.items()])`
    3.  Create an `AIMessage`: `AIMessage(content=f"Lesson generation coming soon! Parameters collected: {param_str}")`.
    4.  Return state update dict: `{"messages": [stub_message]}`.

**Routing Function: `route_parameter_collection` (NEW)**

  * **Logic:**
    1.  Read `required_parameters` from the state.
    2.  If `required_parameters` is empty, return `"generate_lesson"`.
    3.  Otherwise, return `"wait_for_input"`.

**Node: `wait_for_user_input` (NEW)**

  * **Logic:** Empty node that serves as an interrupt point. Returns empty dict `{}`.

#### 4\. File: `app/graph/graph.py`

**Action:** Update graph structure: replace stubs with setups, add collection node, add generate stub, wire edges, and update interrupts.

**Logic:**

1.  **Imports:** Add imports for new nodes and schemas.
2.  **Add/Replace Nodes:**
      * Remove `stub_handwriting_node`, `stub_vocabulary_node`, `stub_idea_generation_node`.
      * `graph.add_node("setup_handwriting", setup_handwriting)`
      * `graph.add_node("setup_vocabulary", setup_vocabulary)`
      * `graph.add_node("setup_idea_generation", setup_idea_generation)`
      * `graph.add_node("collect_parameters", collect_parameters_node)`
      * `graph.add_node("generate_lesson", stub_generate_lesson_node)`
3.  **Update Edges from `main_router`:** Modify the conditional edges to point to the `setup_` nodes:
    ```python
    graph.add_conditional_edges(
        "main_router",
        route_from_main_router,
        {
            "handwriting": "setup_handwriting", # Changed
            "vocabulary": "setup_vocabulary",   # Changed
            "idea_generation": "setup_idea_generation", # Changed
            "clarification": "clarification"
        }
    )
    ```
4.  **Add Edges for Collection Flow:**
      * `graph.add_node("wait_for_input", wait_for_user_input)`
      * `graph.add_edge("setup_handwriting", "collect_parameters")`
      * `graph.add_edge("setup_vocabulary", "collect_parameters")`
      * `graph.add_edge("setup_idea_generation", "collect_parameters")`
      * `graph.add_conditional_edges("collect_parameters", route_parameter_collection, {"wait_for_input": "wait_for_input", "generate_lesson": "generate_lesson"})` \# Route to wait or generate
      * `graph.add_edge("wait_for_input", "collect_parameters")` \# Loop back after user input
      * `graph.add_edge("generate_lesson", END)` \# Connect stub generation to END
5.  **Update Interrupts:** Add `wait_for_input` to the list.
    ```python
    return graph.compile(
        checkpointer=checkpointer,
        interrupt_after=["greeting_node", "clarification", "wait_for_input"] # Added wait_for_input
    )
    ```

<!-- end list -->

  * **Rationale:** The graph now flows from routing -\> task setup -\> parameter collection -\> wait_for_input (interrupt) -\> loop back to collection or proceed to generation. Interrupting after `wait_for_input` ensures the graph pauses after asking each question, waiting for the user's answer.

#### 5\. File: `app/service/chat_service.py`

**Action:** No changes required. The existing resumption logic works with the new interrupt point.

#### 6\. Unit Tests

**File:** Create `tests/test_parameter_collection.py`

  * **Test Setup:** Use dependency override for `ChatService` as established in previous specs.
  * **Test Cases:**
      * **`test_collect_single_parameter_success`:**
        1.  Start with "Handwriting".
        2.  Verify AI asks the grade question with options ("What is the target grade level?...Pre-K, Kindergarten, First Grade.").
        3.  User responds "Kindergarten".
        4.  Verify state: `required_parameters` is empty, `collected_parameters == {"target_grade": "Kindergarten"}`.
        5.  Verify final AI message is the stub generation message.
      * **`test_collect_single_parameter_invalid_choice`:**
        1.  Start with "Vocabulary".
        2.  Verify AI asks the grade question with options.
        3.  User responds "Second Grade".
        4.  Verify AI responds with an error message ("Sorry, I didn't quite understand that...") AND re-asks the *same* grade question with options.
        5.  Verify state: `required_parameters == ["target_grade"]`, `collected_parameters == {}`.
      * **`test_collect_single_parameter_unclear_response`:**
        1.  Start with "Idea Generation".
        2.  Verify AI asks the grade question with options.
        3.  User responds "The older ones".
        4.  Verify AI responds with the same unified error message ("Sorry, I didn't quite understand that...") AND re-asks the *same* grade question with options.
        5.  Verify state: `required_parameters == ["target_grade"]`, `collected_parameters == {}`.
      * **Note:** Both invalid choices and unclear responses now receive the same error message, as the LLM uses `__CLARIFY__` to indicate any input it cannot map to a valid option.
      * **`test_collect_invalid_then_valid`:** Combine the above: invalid response -\> AI re-asks -\> valid response -\> success.

**Run tests:**

```bash
docker compose exec backend pytest tests/test_parameter_collection.py -v
```

#### 7\. LangSmith Evaluation Strategy

  * **Dataset:** "Feature 3: Parameter Collection - Grade"
  * **Examples:** Create examples mirroring the unit test cases (success, invalid choice, unclear response, invalid then valid).
  * **Evaluators:**
    1.  **"Correct Question Asked" (Regex/String Match):** Verify the first question contains "target grade level" and the options "Pre-K", "Kindergarten", "First Grade" (but NOT "__CLARIFY__").
    2.  **"Parameter Extraction Correctness" (Custom Code/JSON):** After valid input ("Kindergarten"), check if `state.collected_parameters['target_grade'] == "Kindergarten"` and `state.required_parameters` is empty.
    3.  **"Invalid/Unclear Input Handling" (Custom Code/JSON + Regex):** After invalid input ("Second Grade") or unclear input ("The older ones"), check if `state.collected_parameters` is still empty, `state.required_parameters == ["target_grade"]`, and the AI response contains "Sorry" and "didn't quite understand" and re-asks the grade question with options. Both cases are now handled identically.

-----
