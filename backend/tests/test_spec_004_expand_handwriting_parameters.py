"""
Unit tests for FEATURE SPEC: 004 - Expand Handwriting Parameters.

Tests that the expanded HandwritingParams schema correctly:
1. Collects query_type parameter with Literal validation
2. Collects target_letters parameter as a string
3. Handles invalid query_type choices with appropriate error messages
4. Handles ambiguous query_type responses with clarification
5. Completes full parameter collection flow for all three parameters
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


def test_collect_handwriting_query_type_invalid(client):
    """
    Test handling of invalid choice for query_type parameter.
    
    Flow:
    1. User: "Hello" -> AI: Greeting
    2. User: "Handwriting" -> AI: Grade question
    3. User: "Kindergarten" -> AI: Query type question with options
    4. User: "reading comprehension" -> AI: Error message + re-ask query_type question
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
    
    # Respond with valid grade
    grade_request = {
        "message": "Kindergarten",
        "thread_id": thread_id
    }
    grade_response = client.post("/api/v1/chat/message", json=grade_request)
    assert grade_response.status_code == 200
    query_type_question = grade_response.json()["reply"]
    
    # Verify AI asks the query_type question
    assert "aspect of handwriting" in query_type_question.lower()
    
    # Respond with invalid query type (unrelated to handwriting)
    invalid_request = {
        "message": "reading comprehension",
        "thread_id": thread_id
    }
    invalid_response = client.post("/api/v1/chat/message", json=invalid_request)
    assert invalid_response.status_code == 200
    error_reply = invalid_response.json()["reply"]
    
    # Verify error message and re-asking
    assert "Sorry" in error_reply
    assert "didn't quite understand" in error_reply or "try again" in error_reply
    assert "aspect of handwriting" in error_reply.lower()
    assert "letter_formation" in error_reply
    assert "fine_motor" in error_reply


def test_collect_handwriting_query_type_clarify(client):
    """
    Test handling of ambiguous response for query_type parameter.
    
    Flow:
    1. User: "Hello" -> AI: Greeting
    2. User: "Handwriting" -> AI: Grade question
    3. User: "Pre-K" -> AI: Query type question with options
    4. User: "help with writing" -> AI: Error message + re-ask query_type question
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
    
    # Respond with valid grade
    grade_request = {
        "message": "Pre-K",
        "thread_id": thread_id
    }
    grade_response = client.post("/api/v1/chat/message", json=grade_request)
    assert grade_response.status_code == 200
    query_type_question = grade_response.json()["reply"]
    
    # Verify AI asks the query_type question
    assert "aspect of handwriting" in query_type_question.lower()
    
    # Respond with ambiguous answer
    unclear_request = {
        "message": "help with writing",
        "thread_id": thread_id
    }
    unclear_response = client.post("/api/v1/chat/message", json=unclear_request)
    assert unclear_response.status_code == 200
    error_reply = unclear_response.json()["reply"]
    
    # Verify error message and re-asking
    assert "Sorry" in error_reply
    assert "didn't quite understand" in error_reply or "try again" in error_reply
    assert "aspect of handwriting" in error_reply.lower()


def test_collect_handwriting_target_letters_success(client):
    """
    Test successful collection of target_letters parameter.
    
    Flow:
    1. User: "Hello" -> AI: Greeting
    2. User: "Handwriting" -> AI: Grade question
    3. User: "First Grade" -> AI: Query type question
    4. User: "spelling" -> AI: Target letters question
    5. User: "x, y, z" -> AI: Stub generation with all params
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
    
    # Respond with valid grade
    grade_request = {
        "message": "First Grade",
        "thread_id": thread_id
    }
    grade_response = client.post("/api/v1/chat/message", json=grade_request)
    assert grade_response.status_code == 200
    
    # Respond with valid query type
    query_type_request = {
        "message": "spelling",
        "thread_id": thread_id
    }
    query_type_response = client.post("/api/v1/chat/message", json=query_type_request)
    assert query_type_response.status_code == 200
    target_letters_question = query_type_response.json()["reply"]
    
    # Verify AI asks the target_letters question
    assert "letter" in target_letters_question.lower()
    
    # Respond with target letters
    target_letters_request = {
        "message": "x, y, z",
        "thread_id": thread_id
    }
    target_letters_response = client.post("/api/v1/chat/message", json=target_letters_request)
    assert target_letters_response.status_code == 200
    final_reply = target_letters_response.json()["reply"]
    
    # Verify success
    assert "Lesson generation coming soon" in final_reply
    assert "First Grade" in final_reply
    assert "spelling" in final_reply
    assert "x, y, z" in final_reply


def test_collect_handwriting_full_flow_invalid_then_valid(client):
    """
    Test full flow with invalid query_type followed by valid responses.
    
    Flow:
    1. User: "Hello" -> AI: Greeting
    2. User: "Handwriting" -> AI: Grade question
    3. User: "Kindergarten" -> AI: Query type question
    4. User: "mathematics" -> AI: Error + re-ask query_type
    5. User: "assessment" -> AI: Target letters question
    6. User: "all letters" -> AI: Stub generation with all params
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
    
    # Respond with valid grade
    grade_request = {
        "message": "Kindergarten",
        "thread_id": thread_id
    }
    grade_response = client.post("/api/v1/chat/message", json=grade_request)
    assert grade_response.status_code == 200
    
    # Respond with invalid query type (completely unrelated topic)
    invalid_query_type_request = {
        "message": "mathematics",
        "thread_id": thread_id
    }
    invalid_query_type_response = client.post("/api/v1/chat/message", json=invalid_query_type_request)
    assert invalid_query_type_response.status_code == 200
    error_reply = invalid_query_type_response.json()["reply"]
    
    # Verify error message
    assert "Sorry" in error_reply
    assert "aspect of handwriting" in error_reply.lower()
    
    # Respond with valid query type
    valid_query_type_request = {
        "message": "assessment",
        "thread_id": thread_id
    }
    valid_query_type_response = client.post("/api/v1/chat/message", json=valid_query_type_request)
    assert valid_query_type_response.status_code == 200
    target_letters_question = valid_query_type_response.json()["reply"]
    
    # Verify target letters question
    assert "letter" in target_letters_question.lower()
    
    # Respond with target letters
    target_letters_request = {
        "message": "all letters",
        "thread_id": thread_id
    }
    target_letters_response = client.post("/api/v1/chat/message", json=target_letters_request)
    assert target_letters_response.status_code == 200
    final_reply = target_letters_response.json()["reply"]
    
    # Verify success
    assert "Lesson generation coming soon" in final_reply
    assert "Kindergarten" in final_reply
    assert "assessment" in final_reply
    assert "all letters" in final_reply
