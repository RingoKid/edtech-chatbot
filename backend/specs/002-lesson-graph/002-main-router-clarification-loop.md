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

#### 2\. File: `app/graph/prompts.py`

**Action:** Add the clarification message constant.

**Content:**

```python
MAIN_ROUTER_CLARIFICATION_MESSAGE = "Sorry, I didn't quite catch that. Could you please specify if you'd like help with Handwriting, Vocabulary, or Idea Generation?"
```

**Action:** Update the system prompt to instruct the LLM about clarification.

```python
MAIN_ROUTER_SYSTEM_PROMPT = "You are a routing assistant. The user must choose one of: Handwriting, Vocabulary, or Idea Generation. Classify their response into exactly one of these three options based on their intent. If the user's intent is unclear or they mention something that doesn't clearly map to one of these three tasks, return '__CLARIFY__' to ask for clarification."
```

#### 3\. File: `app/graph/nodes.py`

**Action:** Update the logic within the `main_router` node and add a new `clarification_node`.

**Node: `main_router`**

  * **Dependencies:** LLM bound to the updated `TaskRoute` schema.
  * **Logic:**
    1.  Get the last message from `state["messages"]`.
    2.  Wrap LLM invocation in a `try...except` block.
    3.  Invoke the structured-output LLM with the user's message.
    4.  **Handle LLM Output:**
          * **On Explicit Clarification (`route.task_name == "__CLARIFY__"`):**
              * Return state update: `{"task_name": "__CLARIFY__"}`.
          * **On Successful Task Classification:**
              * Return state update: `{"task_name": route.task_name}`.
          * **On LLM Invocation Error (in `except` block):**
              * Return state update: `{"task_name": "__CLARIFY__"}`.

**Node: `clarification_node` (NEW)**

  * **Purpose:** Sends the clarification message when user intent is unclear.
  * **Logic:**
    1.  Create clarification `AIMessage` using `MAIN_ROUTER_CLARIFICATION_MESSAGE`.
    2.  Return state update: `{"messages": [clarification_message]}`.

**Action:** Update the `route_from_main_router` function.

**Routing Function: `route_from_main_router`**

  * **Logic:**
    1.  Read `task_name` from state.
    2.  If "Handwriting", return `"handwriting"`.
    3.  If "Vocabulary", return `"vocabulary"`.
    4.  If "Idea Generation", return `"idea_generation"`.
    5.  **If `__CLARIFY__`:** Return `"clarification"`. *(Routes to clarification node)*.
    6.  **If `None` or other:** Return `"clarification"`. *(Fallback)*.

#### 4\. File: `app/graph/graph.py`

**Action:** Add the `clarification` node and update the edges to create the clarification loop.

**Logic:**

1.  **Add the clarification node:**
    ```python
    graph.add_node("clarification", clarification_node)
    ```

2.  **Modify `add_conditional_edges` for main_router:**
    ```python
    graph.add_conditional_edges(
        "main_router",
        route_from_main_router,
        {
            "handwriting": "handwriting",
            "vocabulary": "vocabulary",
            "idea_generation": "idea_generation",
            "clarification": "clarification"  # Route to clarification node
        }
    )
    ```

3.  **Add edge from clarification back to main_router:**
    ```python
    graph.add_edge("clarification", "main_router")  # Loop back to main_router after clarification
    ```

4.  **Update interrupt configuration:**
    ```python
    # Interrupt after greeting_node and clarification node (for clarification loop)
    return graph.compile(checkpointer=checkpointer, interrupt_after=["greeting_node", "clarification"])
    ```

  * **Rationale:** By interrupting after the `clarification` node, the graph pauses after sending the clarification message, allowing the user to respond. The response then triggers the graph to resume at `main_router`, creating the clarification loop.

#### 6\. File: `app/service/chat_service.py`

**Action:** No changes required. The existing resumption logic correctly handles resuming execution after the `clarification` node interrupts.

#### 7\. Unit Tests

**File:** `tests/test_chat_routing.py`

  * **Modify Existing Tests:** 
      * Update `test_routing_with_unclear_input_loops_back` to check for the clarification message containing "Sorry" and the three task options.
      * Update `test_routing_no_manual_if_elif_logic` to include `"clarification"` as a valid route.
  
  * **Add New Tests:**
      * **`test_clarification_loop_success`:** Verify the sequence: 
        1. User: "hi" → AI: (Greeting)
        2. User: "help me plan something" → AI: (Clarification Prompt)
        3. User: "Handwriting" → Graph routes correctly to handwriting node
      
      * **`test_multiple_clarifications`:** Test the loop handles multiple rounds:
        1. User: "hi" → AI: (Greeting)
        2. User: "not sure" → AI: (Clarification)
        3. User: "maybe something else" → AI: (Clarification again)
        4. User: "Vocabulary" → Graph routes correctly to vocabulary node
      
      * **`test_clarification_sets_correct_state`:** Verify that when clarification is needed, `state.task_name == "__CLARIFY__"` and the AI message is the clarification prompt.

**Run tests:**

```bash
docker compose exec backend pytest tests/test_chat_routing.py -v
```

*(Refer to `FEATURE SPEC: 000` for full Docker execution workflow)*

#### 8\. LangSmith Evaluation Strategy

  * **Dataset:** "Feature 2: Router Clarification" (or update "Feature 1")
  * **Examples:** Include multi-turn examples demonstrating the clarification loop.
      * *Example 1:* User: "hi" -\> AI: (Greeting) -\> User: "help me plan" -\> AI: (Clarification) -\> User: "Vocabulary"
      * *Example 2:* User: "hi" -\> AI: (Greeting) -\> User: "not sure" -\> AI: (Clarification) -\> User: "maybe writing?" -\> AI: (Clarification) -\> User: "Idea Generation"
  * **Evaluators:**
    1.  **"Router Correctness" (Updated Custom Evaluator):** Check `task_name` is `__CLARIFY__` after ambiguous input and the correct task name after valid input following clarification. Verify the AI message content matches the clarification prompt.
    2.  **"Clarification Loop Count" (Optional):** Count occurrences of `__CLARIFY__`.

-----

### Implementation Summary

**Key Design Decision:** The implementation uses a dedicated `clarification_node` rather than having `main_router` send the clarification message directly. This approach provides several benefits:

1. **Separation of Concerns:** The `main_router` focuses solely on classification, while `clarification_node` handles messaging.
2. **Proper Interrupts:** By interrupting after `clarification_node`, the graph naturally pauses after sending the clarification message, waiting for user input.
3. **Clean Loop:** The flow is: `main_router` → `clarification_node` (interrupt) → user responds → `main_router` (re-evaluates).

**Graph Flow:**
```
greeting_node → main_router → {
    Handwriting → handwriting → END
    Vocabulary → vocabulary → END
    Idea Generation → idea_generation → END
    __CLARIFY__ → clarification → main_router (loop)
}
```

**Test Results:** All tests passing, including:
- Basic routing to all three task types
- Clarification on ambiguous input
- Single clarification loop success
- Multiple clarification loops
- State management verification

-----
