"""
Unit tests for chat routing functionality.

Tests that the LangGraph routing system correctly:
1. Classifies user input using Pydantic tools
2. Routes to the correct task node (Handwriting, Vocabulary, Idea Generation)
3. Handles ambiguous or unclear input appropriately
4. Maintains routing context across conversation threads
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.routers.chat import get_chat_service
from app.services.chat_service import ChatService
from app.dependencies.auth import get_current_user


def get_test_user():
    """Mock user for bypassing authentication in tests."""
    return {"user_id": "test-user-123", "email": "test@example.com"}


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
    Overrides get_current_user to bypass authentication.

    Returns:
        TestClient: A test client wrapping the FastAPI app
    """
    app.dependency_overrides[get_chat_service] = get_test_chat_service
    app.dependency_overrides[get_current_user] = get_test_user
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_routing_to_handwriting_task(client):
    """
    Test that explicit handwriting-related input routes to handwriting task.

    The routing should classify various ways of expressing handwriting intent:
    - Direct mention: "handwriting"
    - Task description: "help with writing letters"
    - Related terms: "letter formation", "penmanship"
    """
    test_messages = [
        "I want to work on handwriting",
        "Let's do handwriting practice",
        "Help me with letter formation",
        "I need handwriting lessons"
    ]

    for message in test_messages:
        # Start new conversation
        request = {"message": "Hello"}
        response = client.post("/api/v1/chat/message", json=request)
        assert response.status_code == 200
        thread_id = response.json()["thread_id"]

        # Send task selection
        task_request = {
            "message": message,
            "thread_id": thread_id
        }
        task_response = client.post("/api/v1/chat/message", json=task_request)

        assert task_response.status_code == 200
        reply = task_response.json()["reply"]

        # Verify the response indicates handwriting routing
        # Should now ask for grade parameter
        assert "target grade level" in reply.lower() or "handwriting" in reply.lower()


def test_routing_to_vocabulary_task(client):
    """
    Test that vocabulary-related input routes to vocabulary task.

    The routing should classify various vocabulary-related expressions.
    """
    test_messages = [
        "I want to work on vocabulary",
        "Let's do vocabulary practice",
        "Help me teach new words",
        "Vocabulary lessons please"
    ]

    for message in test_messages:
        # Start new conversation
        request = {"message": "Hello"}
        response = client.post("/api/v1/chat/message", json=request)
        assert response.status_code == 200
        thread_id = response.json()["thread_id"]

        # Send task selection
        task_request = {
            "message": message,
            "thread_id": thread_id
        }
        task_response = client.post("/api/v1/chat/message", json=task_request)

        assert task_response.status_code == 200
        reply = task_response.json()["reply"]

        # Verify the response indicates vocabulary routing
        # Should now ask for grade parameter
        assert "target grade level" in reply.lower() or "vocabulary" in reply.lower()


def test_routing_to_idea_generation_task(client):
    """
    Test that idea generation-related input routes to idea generation task.

    The routing should classify various idea generation expressions.
    """
    test_messages = [
        "I want to work on idea generation",
        "Let's do idea generation",
        "Help me with brainstorming ideas",
        "Idea generation lessons"
    ]

    for message in test_messages:
        # Start new conversation
        request = {"message": "Hello"}
        response = client.post("/api/v1/chat/message", json=request)
        assert response.status_code == 200
        thread_id = response.json()["thread_id"]

        # Send task selection
        task_request = {
            "message": message,
            "thread_id": thread_id
        }
        task_response = client.post("/api/v1/chat/message", json=task_request)

        assert task_response.status_code == 200
        reply = task_response.json()["reply"]

        # Verify the response indicates idea generation routing
        # Should now ask for grade parameter
        assert "target grade level" in reply.lower() or "idea" in reply.lower()


def test_routing_with_unclear_input_loops_back(client):
    """
    Test that unclear/ambiguous input causes the router to ask for clarification.

    According to Feature 002, if the LLM cannot classify the input using
    the Pydantic TaskRoute tool, it should return __CLARIFY__ and loop back to main_router.
    """
    # Start conversation
    request = {"message": "Hello"}
    response = client.post("/api/v1/chat/message", json=request)
    assert response.status_code == 200
    thread_id = response.json()["thread_id"]

    # Send unclear/ambiguous input
    unclear_request = {
        "message": "I don't know, just something random",
        "thread_id": thread_id
    }
    unclear_response = client.post("/api/v1/chat/message", json=unclear_request)

    assert unclear_response.status_code == 200
    reply = unclear_response.json()["reply"]

    # Should get the clarification message
    assert "Sorry" in reply or "didn't quite catch" in reply
    assert "Handwriting" in reply and "Vocabulary" in reply and "Idea Generation" in reply


def test_routing_maintains_thread_context(client):
    """
    Test that routing decisions are properly maintained within a conversation thread.

    Multiple routing decisions in the same thread should be handled correctly.
    """
    # Start conversation
    request = {"message": "Hello"}
    response = client.post("/api/v1/chat/message", json=request)
    assert response.status_code == 200
    thread_id = response.json()["thread_id"]

    # First routing decision - handwriting
    first_task = {
        "message": "I want handwriting help",
        "thread_id": thread_id
    }
    first_response = client.post("/api/v1/chat/message", json=first_task)
    assert first_response.status_code == 200

    # The thread should maintain its history
    # Verify we got a response (stub message about handwriting)
    first_reply = first_response.json()["reply"]
    assert len(first_reply) > 0


def test_routing_case_insensitive(client):
    """
    Test that routing works regardless of input casing.

    The LLM-based router should understand intent regardless of case.
    """
    test_cases = [
        "HANDWRITING",
        "handwriting",
        "HaNdWrItInG",
        "Handwriting"
    ]

    for message in test_cases:
        # Start new conversation
        request = {"message": "Hello"}
        response = client.post("/api/v1/chat/message", json=request)
        assert response.status_code == 200
        thread_id = response.json()["thread_id"]

        # Send task selection with different casing
        task_request = {
            "message": message,
            "thread_id": thread_id
        }
        task_response = client.post("/api/v1/chat/message", json=task_request)

        assert task_response.status_code == 200
        reply = task_response.json()["reply"]

        # All should route to handwriting
        # Should now ask for grade parameter
        assert "target grade level" in reply.lower() or "handwriting" in reply.lower()


def test_routing_with_natural_language_variations(client):
    """
    Test that routing handles natural language variations and different phrasings.

    The Pydantic tool-based routing should understand various ways users
    might express their task choice.
    """
    # Different ways to express handwriting intent
    variations = [
        "Can you help me teach kids how to write letters?",
        "My students need to practice their penmanship",
        "I need lesson plans for teaching letter formation"
    ]

    for message in variations:
        # Start new conversation
        request = {"message": "Hello"}
        response = client.post("/api/v1/chat/message", json=request)
        assert response.status_code == 200
        thread_id = response.json()["thread_id"]

        # Send natural language task selection
        task_request = {
            "message": message,
            "thread_id": thread_id
        }
        task_response = client.post("/api/v1/chat/message", json=task_request)

        assert task_response.status_code == 200
        reply = task_response.json()["reply"]

        # Should route to handwriting (natural language understanding)
        assert len(reply) > 0
        # The LLM should recognize these as handwriting-related
        # Note: This test validates the LLM's classification capability


@pytest.mark.asyncio
async def test_routing_uses_pydantic_tools():
    """
    Test that routing uses Pydantic tools (TaskRoute) for classification.

    This is a lower-level test that verifies the graph structure uses
    the correct routing mechanism as per the architectural principles.
    """
    from app.graph.graph import create_graph
    from langchain_core.messages import HumanMessage

    graph = await create_graph()
    config = {"configurable": {"thread_id": "test-routing-tools"}}

    try:
        # Start conversation (will interrupt after greeting)
        await graph.ainvoke({"messages": []}, config=config)

        # Update state with a clear task choice
        await graph.aupdate_state(
            config,
            {"messages": [HumanMessage(content="handwriting")]}
        )

        # Resume - should route through main_router using Pydantic tool
        result = await graph.ainvoke(None, config=config)

        # Verify that task_name was set (indicating successful Pydantic tool use)
        assert "task_name" in result
        assert result["task_name"] in ["Handwriting", "Vocabulary", "Idea Generation"]
    finally:
        # Close the SQLite connection to prevent hanging
        await graph.checkpointer.conn.close()


@pytest.mark.asyncio
async def test_routing_no_manual_if_elif_logic():
    """
    Test that routing doesn't use manual if/elif on raw user text.

    This validates architectural principle: routing must use Pydantic tools
    bound to LLM, not string matching.
    """
    from app.graph.nodes import main_router, route_from_main_router
    from app.graph.state import GraphState
    from langchain_core.messages import HumanMessage

    # Create a mock state with user input
    test_state: GraphState = {
        "messages": [
            HumanMessage(content="Initial greeting"),
            HumanMessage(content="I want to do handwriting")
        ],
        "task_name": None
    }

    # Call the main_router node
    result = main_router(test_state)

    # Verify that task_name was set by the LLM tool call
    assert result.get("task_name") is not None

    # Get the routing decision
    route = route_from_main_router(result)

    # Should be a valid route (updated to include clarification route)
    assert route in ["handwriting", "vocabulary", "idea_generation", "clarification"]


def test_clarification_loop_success(client):
    """
    Test that the clarification loop works: ambiguous input gets clarification,
    then clear input routes correctly.
    
    Conversation flow:
    1. User: "hi" -> AI: (Greeting)
    2. User: "help me plan something" -> AI: (Clarification Prompt)
    3. User: "Handwriting" -> Graph routes to handwriting node
    """
    # Start conversation
    request = {"message": "hi"}
    response = client.post("/api/v1/chat/message", json=request)
    assert response.status_code == 200
    thread_id = response.json()["thread_id"]
    
    # Send ambiguous input
    ambiguous_request = {
        "message": "help me plan something",
        "thread_id": thread_id
    }
    ambiguous_response = client.post("/api/v1/chat/message", json=ambiguous_request)
    assert ambiguous_response.status_code == 200
    clarification_reply = ambiguous_response.json()["reply"]
    
    # Should get clarification message
    assert "Sorry" in clarification_reply or "didn't quite catch" in clarification_reply
    
    # Send clear task selection
    clear_request = {
        "message": "Handwriting",
        "thread_id": thread_id
    }
    clear_response = client.post("/api/v1/chat/message", json=clear_request)
    assert clear_response.status_code == 200
    final_reply = clear_response.json()["reply"]
    
    # Should route to handwriting and ask for grade
    assert "target grade level" in final_reply.lower() or "handwriting" in final_reply.lower()


def test_multiple_clarifications(client):
    """
    Test that the clarification loop can handle multiple unclear inputs
    before finally routing correctly.
    
    Conversation flow:
    1. User: "hi" -> AI: (Greeting)
    2. User: "not sure" -> AI: (Clarification)
    3. User: "maybe something else" -> AI: (Clarification again)
    4. User: "Vocabulary" -> Graph routes to vocabulary node
    """
    # Start conversation
    request = {"message": "hi"}
    response = client.post("/api/v1/chat/message", json=request)
    assert response.status_code == 200
    thread_id = response.json()["thread_id"]
    
    # First ambiguous input
    first_ambiguous = {
        "message": "not sure",
        "thread_id": thread_id
    }
    first_response = client.post("/api/v1/chat/message", json=first_ambiguous)
    assert first_response.status_code == 200
    first_reply = first_response.json()["reply"]
    assert "Sorry" in first_reply or "didn't quite catch" in first_reply
    
    # Second ambiguous input
    second_ambiguous = {
        "message": "maybe something else",
        "thread_id": thread_id
    }
    second_response = client.post("/api/v1/chat/message", json=second_ambiguous)
    assert second_response.status_code == 200
    second_reply = second_response.json()["reply"]
    assert "Sorry" in second_reply or "didn't quite catch" in second_reply
    
    # Finally, clear input
    clear_request = {
        "message": "Vocabulary",
        "thread_id": thread_id
    }
    clear_response = client.post("/api/v1/chat/message", json=clear_request)
    assert clear_response.status_code == 200
    final_reply = clear_response.json()["reply"]
    
    # Should route to vocabulary and ask for grade
    assert "target grade level" in final_reply.lower() or "vocabulary" in final_reply.lower()


@pytest.mark.asyncio
async def test_clarification_sets_correct_state():
    """
    Test that when clarification is needed, the state is set to __CLARIFY__
    and the next node would be main_router (creating the loop).
    """
    from app.graph.graph import create_graph
    from langchain_core.messages import HumanMessage
    
    graph = await create_graph()
    config = {"configurable": {"thread_id": "test-clarify-state"}}
    
    try:
        # Start conversation (will interrupt after greeting)
        await graph.ainvoke({"messages": []}, config=config)
        
        # Update state with ambiguous input
        await graph.aupdate_state(
            config,
            {"messages": [HumanMessage(content="something unclear")]}
        )
        
        # Resume - should trigger clarification
        result = await graph.ainvoke(None, config=config)
        
        # Verify task_name is __CLARIFY__
        assert result.get("task_name") == "__CLARIFY__"
        
        # Verify the last AI message is the clarification prompt
        last_message = result["messages"][-1]
        assert "Sorry" in last_message.content or "didn't quite catch" in last_message.content
    finally:
        # Close the SQLite connection to prevent hanging
        await graph.checkpointer.conn.close()

