Okay dude, got it. Providing the common spec (`000`) every time is the right way to keep things consistent.

Here's the combined spec file for Feature 002, incorporating the common project rules and removing the redundant execution instructions.

-----

### FEATURE SPEC: 000 - Project Common

*(Included for context - see original file for full content)*

  * **Core Architectural Principles:** LangGraph, Unified State, Pydantic Tool Routing, `interrupt_after` Pausing.
  * **Execution Environment:** All commands via `docker compose exec backend ...`
  * **Workflow:** Implement -\> Rebuild (`docker compose down && docker compose up -d --build`) -\> Test (`docker compose exec backend pytest ...`) -\> Fix -\> Sync Spec.

-----

### FEATURE SPEC: 002 - Main Router Clarification Loop

**Objective:** Modify the `main_router` node to handle ambiguous user input. If the LLM cannot confidently classify the user's choice into one of the valid tasks, the node should ask for clarification and route the conversation back to itself to re-evaluate the user's *next* response.

#### 1\. File: `app/schemas/task_route.py`

**Action:** Modify the `TaskRoute` Pydantic model. Add `"__CLARIFY__"` as a possible literal value for `task_name`.

**Content:**

```python
# [Modify Schema]
from pydantic import BaseModel, Field
from typing import Literal

class TaskRoute(BaseModel):
    """
    Routes the user's request to the correct lesson planning task or indicates clarification is needed.
    """
    task_name: Literal["Handwriting", "Vocabulary", "Idea Generation", "__CLARIFY__"] = Field(
        ...,
        description="The specific lesson planning task the user wants to start, or '__CLARIFY__' if the user's intent is unclear."
    )

```

  * **Rationale:** Adding `__CLARIFY__` allows the LLM to explicitly signal ambiguity.

#### 2\. File: `app/graph/nodes.py`

**Action:** Update the logic within the `main_router` node.

**Node: `main_router`**

  * **Dependencies:** LLM bound to the updated `TaskRoute` schema.
  * **Logic:**
    1.  Get the last message from `state["messages"]`.
    2.  Wrap LLM invocation in a `try...except` block.
    3.  Invoke the structured-output LLM with the user's message.
    4.  **Handle LLM Output:**
          * **On Explicit Clarification (`route.task_name == "__CLARIFY__"`):**
              * Create clarification `AIMessage`: "Sorry, I didn't quite catch that. Could you please specify if you'd like help with Handwriting, Vocabulary, or Idea Generation?"
              * Return state update: `{"messages": [clarification_message], "task_name": "__CLARIFY__"}`.
          * **On Successful Task Classification:**
              * Return state update: `{"task_name": route.task_name}`.
          * **On LLM Invocation Error (in `except` block):**
              * Create the same clarification `AIMessage`.
              * Return state update: `{"messages": [clarification_message], "task_name": "__CLARIFY__"}`.

**Action:** Update the `route_from_main_router` function.

**Routing Function: `route_from_main_router`**

  * **Logic:**
    1.  Read `task_name` from state.
    2.  If "Handwriting", return `"handwriting"`.
    3.  If "Vocabulary", return `"vocabulary"`.
    4.  If "Idea Generation", return `"idea_generation"`.
    5.  **If `__CLARIFY__` or `None`:** Return `"main_router"`. *(Creates the loop)*.

#### 3\. File: `app/graph/graph.py`

**Action:** Update the conditional edges for the `main_router`.

**Logic:**

1.  **Modify `add_conditional_edges`:**
    ```python
    # [Modify Edge Logic]
    graph.add_conditional_edges(
        "main_router",
        route_from_main_router,
        {
            "handwriting": "handwriting",
            "vocabulary": "vocabulary",
            "idea_generation": "idea_generation",
            "main_router": "main_router" # Added loop back
        }
    )
    ```

#### 4\. File: `app/service/chat_service.py`

**Action:** No changes required.

#### 5\. Testing Considerations (Descriptions Only)

**File:** `tests/test_chat_routing.py`

  * **Modify Existing Tests:** Ensure tests expecting the old error loop now check for `task_name == "__CLARIFY__"` and the correct clarification message. Assert the next node would be `main_router`.
  * **Add New Tests:**
      * **Clarification Loop Success:** Verify the sequence: ambiguous input -\> clarification prompt -\> valid input -\> correct task node.
      * **Multiple Clarifications:** Test the loop handles several rounds of ambiguous input before succeeding.

*(Refer to `FEATURE SPEC: 000` for how to execute these tests using Docker)*

#### 6\. LangSmith Evaluation Strategy

  * **Dataset:** "Feature 2: Router Clarification" (or update "Feature 1")
  * **Examples:** Include multi-turn examples demonstrating the clarification loop.
      * *Example 1:* User: "hi" -\> AI: (Greeting) -\> User: "help me plan" -\> AI: (Clarification) -\> User: "Vocabulary"
      * *Example 2:* User: "hi" -\> AI: (Greeting) -\> User: "not sure" -\> AI: (Clarification) -\> User: "maybe writing?" -\> AI: (Clarification) -\> User: "Idea Generation"
  * **Evaluators:**
    1.  **"Router Correctness" (Updated Custom Evaluator):** Check `task_name` is `__CLARIFY__` after ambiguous input and the correct task name after valid input following clarification. Verify the AI message content matches the clarification prompt.
    2.  **"Clarification Loop Count" (Optional):** Count occurrences of `__CLARIFY__`.

-----
