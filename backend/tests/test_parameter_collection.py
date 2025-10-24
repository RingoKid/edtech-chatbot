"""
Unit tests for dynamic parameter collection functionality.

Tests that the parameter collection system correctly:
1. Asks questions based on schema field descriptions
2. Extracts and validates user responses
3. Handles invalid choices with appropriate error messages
4. Handles unclear responses with appropriate error messages
5. Loops until all required parameters are collected
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
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

    Returns:
        TestClient: A test client wrapping the FastAPI app
    """
    app.dependency_overrides[get_chat_service] = get_test_chat_service
    client = TestClient(app)
    yield client
    app.dependency_overrides.clear()


def test_collect_single_parameter_success(client):
    """
    Test successful collection of the target_grade parameter.
    
    Flow:
    1. User: "Hello" -> AI: Greeting
    2. User: "Handwriting" -> AI: Grade question with options
    3. User: "Kindergarten" -> AI: Stub generation message with collected params
    """
    # Start conversation
    request = {"message": "Hello"}
    response = client.post("/api/v1/chat/message", json=request)
    assert response.status_code == 200
    thread_id = response.json()["thread_id"]
    
    # Select handwriting task
    task_request = {
        "message": "Handwriting",
        "thread_id": thread_id
    }
    task_response = client.post("/api/v1/chat/message", json=task_request)
    assert task_response.status_code == 200
    grade_question = task_response.json()["reply"]
    
    # Verify AI asks the grade question with options
    assert "target grade level" in grade_question.lower()
    assert "Pre-K" in grade_question
    assert "Kindergarten" in grade_question
    assert "First Grade" in grade_question
    
    # Respond with valid grade
    grade_request = {
        "message": "Kindergarten",
        "thread_id": thread_id
    }
    grade_response = client.post("/api/v1/chat/message", json=grade_request)
    assert grade_response.status_code == 200
    final_reply = grade_response.json()["reply"]
    
    # Verify we get the stub generation message with collected params
    assert "Lesson generation coming soon" in final_reply
    assert "Kindergarten" in final_reply


def test_collect_single_parameter_invalid_choice(client):
    """
    Test handling of invalid choice for target_grade parameter.
    
    Flow:
    1. User: "Hello" -> AI: Greeting
    2. User: "Vocabulary" -> AI: Grade question with options
    3. User: "Second Grade" -> AI: Error message + re-ask grade question
    """
    # Start conversation
    request = {"message": "Hello"}
    response = client.post("/api/v1/chat/message", json=request)
    assert response.status_code == 200
    thread_id = response.json()["thread_id"]
    
    # Select vocabulary task
    task_request = {
        "message": "Vocabulary",
        "thread_id": thread_id
    }
    task_response = client.post("/api/v1/chat/message", json=task_request)
    assert task_response.status_code == 200
    grade_question = task_response.json()["reply"]
    
    # Verify AI asks the grade question
    assert "target grade level" in grade_question.lower()
    
    # Respond with invalid grade
    invalid_request = {
        "message": "Second Grade",
        "thread_id": thread_id
    }
    invalid_response = client.post("/api/v1/chat/message", json=invalid_request)
    assert invalid_response.status_code == 200
    error_reply = invalid_response.json()["reply"]
    
    # Verify error message and re-asking
    assert "Sorry" in error_reply
    assert "didn't quite understand" in error_reply or "try again" in error_reply
    assert "target grade level" in error_reply.lower()
    assert "Pre-K" in error_reply
    assert "Kindergarten" in error_reply
    assert "First Grade" in error_reply


def test_collect_single_parameter_unclear_response(client):
    """
    Test handling of unclear/ambiguous response for target_grade parameter.
    
    Flow:
    1. User: "Hello" -> AI: Greeting
    2. User: "Idea Generation" -> AI: Grade question with options
    3. User: "The older ones" -> AI: Error message + re-ask grade question
    """
    # Start conversation
    request = {"message": "Hello"}
    response = client.post("/api/v1/chat/message", json=request)
    assert response.status_code == 200
    thread_id = response.json()["thread_id"]
    
    # Select idea generation task
    task_request = {
        "message": "Idea Generation",
        "thread_id": thread_id
    }
    task_response = client.post("/api/v1/chat/message", json=task_request)
    assert task_response.status_code == 200
    grade_question = task_response.json()["reply"]
    
    # Verify AI asks the grade question
    assert "target grade level" in grade_question.lower()
    
    # Respond with unclear answer
    unclear_request = {
        "message": "The older ones",
        "thread_id": thread_id
    }
    unclear_response = client.post("/api/v1/chat/message", json=unclear_request)
    assert unclear_response.status_code == 200
    error_reply = unclear_response.json()["reply"]
    
    # Verify error message and re-asking
    assert "Sorry" in error_reply
    assert "didn't quite understand" in error_reply or "try again" in error_reply
    assert "target grade level" in error_reply.lower()


def test_collect_invalid_then_valid(client):
    """
    Test recovery from invalid input: invalid response -> valid response -> success.
    
    Flow:
    1. User: "Hello" -> AI: Greeting
    2. User: "Handwriting" -> AI: Grade question
    3. User: "Third Grade" -> AI: Error + re-ask
    4. User: "Pre-K" -> AI: Stub generation with collected params
    """
    # Start conversation
    request = {"message": "Hello"}
    response = client.post("/api/v1/chat/message", json=request)
    assert response.status_code == 200
    thread_id = response.json()["thread_id"]
    
    # Select handwriting task
    task_request = {
        "message": "Handwriting",
        "thread_id": thread_id
    }
    task_response = client.post("/api/v1/chat/message", json=task_request)
    assert task_response.status_code == 200
    
    # Respond with invalid grade
    invalid_request = {
        "message": "Third Grade",
        "thread_id": thread_id
    }
    invalid_response = client.post("/api/v1/chat/message", json=invalid_request)
    assert invalid_response.status_code == 200
    error_reply = invalid_response.json()["reply"]
    
    # Verify error message
    assert "Sorry" in error_reply
    
    # Respond with valid grade
    valid_request = {
        "message": "Pre-K",
        "thread_id": thread_id
    }
    valid_response = client.post("/api/v1/chat/message", json=valid_request)
    assert valid_response.status_code == 200
    final_reply = valid_response.json()["reply"]
    
    # Verify success
    assert "Lesson generation coming soon" in final_reply
    assert "Pre-K" in final_reply


@pytest.mark.asyncio
async def test_parameter_collection_state():
    """
    Test that parameter collection correctly manages state.
    
    Verifies:
    - parameter_schema is set
    - required_parameters starts with ["target_grade"]
    - collected_parameters accumulates values
    - required_parameters becomes empty when done
    """
    from app.graph.graph import create_graph
    from langchain_core.messages import HumanMessage
    
    graph = await create_graph()
    config = {"configurable": {"thread_id": "test-param-state"}}
    
    try:
        # Start conversation (will interrupt after greeting)
        await graph.ainvoke({"messages": []}, config=config)
        
        # Select handwriting task
        await graph.aupdate_state(
            config,
            {"messages": [HumanMessage(content="Handwriting")]}
        )
        
        # Resume - should go through main_router -> setup_handwriting -> collect_parameters
        await graph.ainvoke(None, config=config)
        
        # Get state after setup
        state = await graph.aget_state(config)
        result = state.values
        
        # Verify state after setup
        assert result.get("parameter_schema_name") == "HandwritingParams"
        assert result.get("required_parameters") == ["target_grade"]
        assert result.get("collected_parameters") == {}
        
        # Provide valid grade
        await graph.aupdate_state(
            config,
            {"messages": [HumanMessage(content="Kindergarten")]}
        )
        
        # Resume - should extract and validate
        await graph.ainvoke(None, config=config)
        
        # Get state after collection
        state = await graph.aget_state(config)
        result = state.values
        
        # Verify state after collection
        assert result.get("required_parameters") == []
        assert result.get("collected_parameters") == {"target_grade": "Kindergarten"}
        
        # Verify final message is stub generation
        last_message = result["messages"][-1]
        assert "Lesson generation coming soon" in last_message.content
        assert "Kindergarten" in last_message.content
    finally:
        # Close the SQLite connection to prevent hanging
        await graph.checkpointer.conn.close()


@pytest.mark.asyncio
async def test_parameter_collection_uses_dynamic_schema():
    """
    Test that parameter collection dynamically creates single-field models
    for extraction and validation.
    """
    from app.graph.graph import create_graph
    from langchain_core.messages import HumanMessage
    
    graph = await create_graph()
    config = {"configurable": {"thread_id": "test-dynamic-schema"}}
    
    try:
        # Start and select vocabulary task
        await graph.ainvoke({"messages": []}, config=config)
        await graph.aupdate_state(
            config,
            {"messages": [HumanMessage(content="Vocabulary")]}
        )
        await graph.ainvoke(None, config=config)
        
        # Get state to verify question is asked
        state = await graph.aget_state(config)
        result = state.values
        last_message = result["messages"][-1]
        assert "target grade level" in last_message.content.lower()
        
        # Provide invalid choice - should be caught by dynamic schema validation
        await graph.aupdate_state(
            config,
            {"messages": [HumanMessage(content="High School")]}
        )
        await graph.ainvoke(None, config=config)
        
        # Get state to verify error handling
        state = await graph.aget_state(config)
        result = state.values
        last_message = result["messages"][-1]
        assert "Sorry" in last_message.content
        
        # State should not have collected the invalid value
        assert result.get("collected_parameters") == {}
        assert result.get("required_parameters") == ["target_grade"]
    finally:
        # Close the SQLite connection to prevent hanging
        await graph.checkpointer.conn.close()
