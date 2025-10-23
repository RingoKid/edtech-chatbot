### FEATURE SPEC: 001 - Greeting & Main Router

**Objective:** Implement the initial graph entry flow. The graph must greet the user, present main tasks, pause for input, and robustly classify the user's choice. If classification fails, it must loop back and re-prompt the user.

#### 1. File: \`app/schemas/task_route.py\`

**Action:** Create a new Pydantic model \`TaskRoute\`.

**Content:**
```python
# [New Schema]
from pydantic import BaseModel, Field
from typing import Literal

class TaskRoute(BaseModel):
    """
    Routes the user's request to the correct lesson planning task.
    """
    task_name: Literal["Handwriting", "Vocabulary", "Idea Generation"] = Field(
        ..., 
        description="The specific lesson planning task the user wants to start."
    )
```

#### 2. File: \`app/graph/state.py\`

**Action:** Define the initial \`GraphState\`.

**Content:**
```python
# [New Schema]
from typing import TypedDict, Annotated, List
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

class GraphState(TypedDict):
    """
    The unified state object for the entire graph.
    """
    # Messages are handled with add_messages reducer
    messages: Annotated[List[BaseMessage], add_messages]
    
    # This key will be populated by the main_router
    task_name: str 
```
*Note: The \`messages\` field uses the \`add_messages\` reducer for correct, stateful message list management.*

#### 3. File: \`app/graph/nodes.py\`

**Action:** Create \`greeting_node\`, \`main_router\`, stub nodes, and the routing function.

**Node: \`greeting_node\`**
* **Logic:**
    1.  Create an \`AIMessage\` with the welcome text: "Welcome! I'm here to help you build lesson plans. \n\nWhat would you like to work on?\n- Handwriting\n- Vocabulary\n- Idea Generation"
    2.  Return a state update dict: \`{"messages": [welcome_message]}\`.
    * *Note: The \`add_messages\` reducer handles appending this to the state.*

**Node: \`main_router\`**
* **Dependencies:** Needs an LLM bound to the \`TaskRoute\` schema (e.g., \`llm.with_structured_output(TaskRoute)\`).
* **Logic:**
    1.  Get the *last message* from \`state["messages"]\` (this is the user's choice).
    2.  Invoke the structured-output LLM with the user's message.
    3.  **On Success (LLM returns a valid \`TaskRoute\` object):**
        * Return a state update dict: \`{"task_name": route.task_name}\`.
    4.  **On Failure (LLM throws an error, e.g., Pydantic validation fails on "spanish"):**
        * Create an error \`AIMessage\`: "I'm sorry, I didn't understand that choice. Can you please pick from Handwriting, Vocabulary, or Idea Generation?"
        * Return a state update dict: \`{"messages": [error_message], "task_name": "__ERROR__"}\`.
* **Note on Change:** *All brittle keyword-checking logic has been REMOVED per our architectural principles. We trust the Pydantic tool-call failure.*

**Stub Nodes: \`stub_handwriting_node\`, \`stub_vocabulary_node\`, \`stub_idea_generation_node\`**
* **Logic (Example for Handwriting):**
    1.  Create an \`AIMessage\`: \`AIMessage(content="*Handwriting feature coming soon!*")\`.
    2.  Return state update dict: \`{"messages": [stub_message]}\`.

**Routing Function: \`route_from_main_router\`**
* **Logic:**
    1.  Read \`task_name\` from the state using \`state.get("task_name")\`.
    2.  If "Handwriting", return \`"handwriting"\`.
    3.  If "Vocabulary", return \`"vocabulary"\`.
    4.  If "Idea Generation", return \`"idea_generation"\`.
    5.  **Note on Change:** If \`__ERROR__\` or \`None\`, return \`"greeting_node"\`.
    * *This creates the self-correcting loop we discussed.*

#### 4. File: \`app/graph/graph.py\`

**Action:** Define the graph structure and compile with a persistent \`SqliteSaver\`.

**Logic:**
1.  **Import:** \`from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver\` and \`import aiosqlite\`
2.  **Checkpointer:** Instantiate the checkpointer:
    ```python
    conn = await aiosqlite.connect("checkpointer.sqlite")
    checkpointer = AsyncSqliteSaver(conn)
    await checkpointer.setup()
    ```
    * *Note on Change: Using \`AsyncSqliteSaver\` for persistent, shareable state with async support, replacing DynamoDB for local dev.*
    * *Note: We create an aiosqlite connection first, then pass it to AsyncSqliteSaver, then call setup() to initialize the database schema.*
3.  **Graph:** Instantiate \`StateGraph(GraphState)\`.
4.  **Add Nodes:**
    * \`graph.add_node("greeting_node", greeting_node)\`
    * \`graph.add_node("main_router", main_router)\`
    * \`graph.add_node("handwriting", stub_handwriting_node)\`
    * \`graph.add_node("vocabulary", stub_vocabulary_node)\`
    * \`graph.add_node("idea_generation", stub_idea_generation_node)\`
5.  **Add Edges:**
    * \`graph.set_entry_point("greeting_node")\`
    * \`graph.add_edge("greeting_node", "main_router")\`
    * \`graph.add_conditional_edges("main_router", route_from_main_router, {"handwriting": "handwriting", "vocabulary": "vocabulary", "idea_generation": "idea_generation", "greeting_node": "greeting_node"})\`
    * \`graph.add_edge("handwriting", END)\`
    * \`graph.add_edge("vocabulary", END)\`
    * \`graph.add_edge("idea_generation", END)\`
6.  **Compile Graph:**
    * Call \`graph.compile(checkpointer=checkpointer, interrupt_after=["greeting_node"])\`.
    * *Note: \`interrupt_after\` is the correct parameter name (not \`interrupt_after_nodes\`).*
    * *Note: Since we're using \`AsyncSqliteSaver\`, the graph creation should be wrapped in an async function that can be awaited.*

#### 4a. File: \`app/routers/chat.py\`

**Action:** Implement singleton pattern for ChatService to ensure the same graph instance (with persistent checkpointer) is shared across all API requests.

**Logic:**
1.  **Import:** \`from functools import lru_cache\`
2.  **Dependency Function:** Implement \`get_chat_service()\` using \`lru_cache\` for singleton pattern:
    ```python
    @lru_cache(maxsize=1)
    def get_chat_service() -> ChatService:
        """
        Returns a singleton ChatService instance for the application lifecycle.
        Uses lru_cache to ensure only one instance is created and reused across requests.
        Can be overridden in tests via dependency injection to avoid event loop conflicts.
        """
        return ChatService()
    ```
    * *Note: \`@lru_cache(maxsize=1)\` provides a cleaner singleton pattern than global variables. With \`maxsize=1\`, the function caches its result and returns the same \`ChatService\` instance on all subsequent calls.*
    * *Note: This is CRITICAL for persistence. Without this, each API request would create a new graph with a new database connection, breaking state persistence.*
    * *Note: This can be overridden in tests using \`app.dependency_overrides\` to provide fresh instances per test, avoiding asyncio event loop conflicts.*

#### 4b. File: \`app/service/chat_service.py\`

**Action:** Implement proper graph resumption logic to handle interrupted conversations.

**Logic in \`handle_message()\`:**
1.  **Get Graph:** Call \`graph = await self._get_graph()\` (lazy initialization)
2.  **Thread ID:** If no \`thread_id\` provided, create new one
3.  **Config:** Create config dict: \`{"configurable": {"thread_id": thread_id}}\`
4.  **Check State:** Call \`current_state = await graph.aget_state(config)\`
5.  **Conditional Invocation:**
    * **If \`current_state\` exists and \`current_state.next\` is truthy** (thread is interrupted):
        * Call \`await graph.aupdate_state(config, {"messages": [HumanMessage(content=user_message)]})\` to add user's message
        * Call \`result = await graph.ainvoke(None, config=config)\` to resume from checkpoint
    * **Else** (new thread or completed thread):
        * Create input state: \`{"messages": [HumanMessage(content=user_message)]}\`
#### 5. Testing Considerations

**Event Loop Conflict Resolution:**
The singleton \`ChatService\` instance binds to the event loop that exists when it's first created. In production, this is fine (one event loop for the app lifetime). However, pytest creates fresh event loops per test, causing \`RuntimeError: attached to a different event loop\` if tests try to use the cached singleton.

**Solution: Dependency Override in Tests**

In test files, override \`get_chat_service()\` to provide fresh instances:

```python
from app.routers.chat import get_chat_service
from app.service.chat_service import ChatService

def get_test_chat_service() -> ChatService:
    """
    Creates a fresh ChatService instance for each test.
    This avoids event loop conflicts when the singleton is reused across tests.
    """
    return ChatService()

@pytest.fixture
def client():
    """
    Pytest fixture that creates a TestClient instance for testing.
    Overrides the get_chat_service dependency to provide fresh instances per test.
    """
    app.dependency_overrides[get_chat_service] = get_test_chat_service
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()
```

**Why This Works:**
* Production: Singleton runs with stable event loop throughout app lifetime
* Tests: Each test gets fresh \`ChatService\` with current test's event loop
* Graph persistence still works via the SQLite checkpointer (thread_id based)

**Important Note on \`main_router\` Node:**
The \`main_router\` node is a **synchronous function** that uses \`.invoke()\` (not \`.ainvoke()\`) to call the LLM. When testing it directly:
```python
# Correct - no await
result = main_router(test_state)

# Incorrect - will raise TypeError
result = await main_router(test_state)
```

#### 6. LangSmith Evaluation Strategy
6.  **Extract Response:** Get the last message from \`result["messages"]\`

* *Note on Change: This is the CORRECT LangGraph pattern for handling interrupted graphs with persistent checkpointers. Using \`ainvoke()\` with full state always replaces the state, which would restart the conversation. The \`aget_state()\` + \`aupdate_state()\` + \`ainvoke(None)\` pattern properly resumes from the interrupted checkpoint.*

#### 5. Unit Tests

**File:** \`tests/test_chat_message_api.py\`
Tests the REST API endpoint for chat messages:
* New thread creation (without thread_id)
* Continuing conversations (with thread_id)
* Request validation (missing/empty fields)
* Response schema validation
* Custom thread IDs, long messages, special characters

**File:** \`tests/test_chat_routing.py\`
Tests the routing functionality:
* Routes to correct task (Handwriting, Vocabulary, Idea Generation)
* Handles ambiguous input (loops back to greeting)
* Case-insensitive routing
* Natural language variations
* Validates Pydantic tool usage (no manual if/elif)

**Run tests:**
```bash
docker compose exec backend pytest tests/test_chat_message_api.py -v
docker compose exec backend pytest tests/test_chat_routing.py -v
```

#### 6. LangSmith Evaluation Strategy

* **Dataset:** "Feature 1: Main Routing"
* **Examples:** Create ~20 examples, each with two turns (or more for failure cases).
    * **Success Case:**
        * Turn 1 (User): "hi"
        * Turn 2 (User): "I want to do handwriting"
    * **Failure Loop Case:**
        * Turn 1 (User): "hi"
        * Turn 2 (User): "let's do spanish"
* **Evaluators:**
    1.  **"Router Correctness" (Custom Evaluator):**
        * For "handwriting" input, assert \`state.task_name == "Handwriting"\`.
        * For "spanish" input, assert \`state.task_name == "__ERROR__"\`.
    2.  **"Welcome Message" (Regex Match):**
        * Checks \`state.messages[1]\` (the first AI message).
        * Asserts its content matches "Welcome! I'm here to help...".
    3.  **"Failure Loop" (Custom Evaluator):**
        * For "spanish" input, run the graph to completion.
        * Assert that the *last* message in \`state.messages\` is the "Welcome!..." greeting, proving the loop back to \`greeting_node\` was successful.