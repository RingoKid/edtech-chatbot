"""
Unit tests for dynamic parameter collection across all task types.

Tests that the parameter collection system correctly handles:
- Vocabulary task parameters (query_type, target_vocabulary, target_genre)
- Idea Generation task parameters (query_type, target_genre, target_topic)
- Invalid/unclear inputs for Literal fields
- Full successful flows for all task types
"""
import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.routers.chat import get_chat_service
from app.services.chat_service import ChatService


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


# ============================================================================
# VOCABULARY TESTS
# ============================================================================

def test_collect_vocabulary_success(client):
    """
    Test successful collection of all vocabulary parameters.
    
    Flow:
    1. User: "Hello" -> AI: Greeting
    2. User: "Vocabulary" -> AI: Grade question
    3. User: "Kindergarten" -> AI: Query type question
    4. User: "vocabulary_building" -> AI: Target vocabulary question
    5. User: "colors" -> AI: Target genre question
    6. User: "Not applicable" -> AI: Stub generation message with collected params
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
    query_type_question = grade_response.json()["reply"]
    
    # Verify AI asks the query_type question with options
    assert "aspect of vocabulary" in query_type_question.lower() or "syntax" in query_type_question.lower()
    assert "sentence structure" in query_type_question
    assert "vocabulary building" in query_type_question
    assert "grammar" in query_type_question
    assert "genre writing" in query_type_question
    assert "general" in query_type_question
    assert "__CLARIFY__" not in query_type_question
    
    # Respond with valid query type
    query_type_request = {
        "message": "vocabulary building",
        "thread_id": thread_id
    }
    query_type_response = client.post("/api/v1/chat/message", json=query_type_request)
    assert query_type_response.status_code == 200
    target_vocab_question = query_type_response.json()["reply"]
    
    # Verify AI asks the target_vocabulary question
    assert "vocabulary words" in target_vocab_question.lower() or "concepts" in target_vocab_question.lower()
    
    # Respond with target vocabulary
    target_vocab_request = {
        "message": "colors",
        "thread_id": thread_id
    }
    target_vocab_response = client.post("/api/v1/chat/message", json=target_vocab_request)
    assert target_vocab_response.status_code == 200
    target_genre_question = target_vocab_response.json()["reply"]
    
    # Verify AI asks the target_genre question
    assert "genre" in target_genre_question.lower()
    
    # Respond with target genre
    target_genre_request = {
        "message": "Not applicable",
        "thread_id": thread_id
    }
    target_genre_response = client.post("/api/v1/chat/message", json=target_genre_request)
    assert target_genre_response.status_code == 200
    final_reply = target_genre_response.json()["reply"]
    
    # Verify we get the stub generation message with collected params
    assert "Lesson generation coming soon" in final_reply
    assert "Kindergarten" in final_reply
    assert "vocabulary building" in final_reply
    assert "colors" in final_reply
    assert "Not applicable" in final_reply


def test_collect_vocabulary_query_type_invalid(client):
    """
    Test handling of invalid choice for vocabulary query_type parameter.
    
    Flow:
    1. User: "Hello" -> AI: Greeting
    2. User: "Vocabulary" -> AI: Grade question
    3. User: "Pre-K" -> AI: Query type question
    4. User: "reading comprehension" -> AI: Error message + re-ask query type question
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
    
    # Respond with valid grade
    grade_request = {
        "message": "Pre-K",
        "thread_id": thread_id
    }
    grade_response = client.post("/api/v1/chat/message", json=grade_request)
    assert grade_response.status_code == 200
    query_type_question = grade_response.json()["reply"]
    
    # Verify query type question
    assert "aspect of vocabulary" in query_type_question.lower() or "syntax" in query_type_question.lower()
    
    # Respond with invalid query type
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
    assert "aspect of vocabulary" in error_reply.lower() or "syntax" in error_reply.lower()


def test_collect_vocabulary_target_genre_handling(client):
    """
    Test that target_genre (string field) is collected correctly for vocabulary.
    
    Flow:
    1. User: "Hello" -> AI: Greeting
    2. User: "Vocabulary" -> AI: Grade question
    3. User: "First Grade" -> AI: Query type question
    4. User: "genre_writing" -> AI: Target vocabulary question
    5. User: "None" -> AI: Target genre question
    6. User: "narrative" -> AI: Stub generation with all params
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
    
    # Respond with valid grade
    grade_request = {
        "message": "First Grade",
        "thread_id": thread_id
    }
    grade_response = client.post("/api/v1/chat/message", json=grade_request)
    assert grade_response.status_code == 200
    
    # Respond with query type
    query_type_request = {
        "message": "genre writing",
        "thread_id": thread_id
    }
    query_type_response = client.post("/api/v1/chat/message", json=query_type_request)
    assert query_type_response.status_code == 200
    
    # Respond with target vocabulary
    target_vocab_request = {
        "message": "None",
        "thread_id": thread_id
    }
    target_vocab_response = client.post("/api/v1/chat/message", json=target_vocab_request)
    assert target_vocab_response.status_code == 200
    target_genre_question = target_vocab_response.json()["reply"]
    
    # Verify target genre question
    assert "genre" in target_genre_question.lower()
    
    # Respond with target genre
    target_genre_request = {
        "message": "narrative",
        "thread_id": thread_id
    }
    target_genre_response = client.post("/api/v1/chat/message", json=target_genre_request)
    assert target_genre_response.status_code == 200
    final_reply = target_genre_response.json()["reply"]
    
    # Verify success
    assert "Lesson generation coming soon" in final_reply
    assert "First Grade" in final_reply
    assert "genre writing" in final_reply
    assert "narrative" in final_reply


def test_collect_vocabulary_invalid_then_valid(client):
    """
    Test recovery from invalid input for vocabulary task.
    
    Flow:
    1. User: "Hello" -> AI: Greeting
    2. User: "Vocabulary" -> AI: Grade question
    3. User: "Kindergarten" -> AI: Query type question
    4. User: "phonics" -> AI: Error + re-ask
    5. User: "grammar" -> AI: Target vocabulary question
    6. User: "action verbs" -> AI: Target genre question
    7. User: "Not applicable" -> AI: Stub generation
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
    
    # Respond with valid grade
    grade_request = {
        "message": "Kindergarten",
        "thread_id": thread_id
    }
    grade_response = client.post("/api/v1/chat/message", json=grade_request)
    assert grade_response.status_code == 200
    
    # Respond with invalid query type
    invalid_request = {
        "message": "phonics",
        "thread_id": thread_id
    }
    invalid_response = client.post("/api/v1/chat/message", json=invalid_request)
    assert invalid_response.status_code == 200
    error_reply = invalid_response.json()["reply"]
    
    # Verify error message
    assert "Sorry" in error_reply
    
    # Respond with valid query type
    valid_request = {
        "message": "grammar",
        "thread_id": thread_id
    }
    valid_response = client.post("/api/v1/chat/message", json=valid_request)
    assert valid_response.status_code == 200
    
    # Respond with target vocabulary
    target_vocab_request = {
        "message": "action verbs",
        "thread_id": thread_id
    }
    target_vocab_response = client.post("/api/v1/chat/message", json=target_vocab_request)
    assert target_vocab_response.status_code == 200
    
    # Respond with target genre
    target_genre_request = {
        "message": "Not applicable",
        "thread_id": thread_id
    }
    target_genre_response = client.post("/api/v1/chat/message", json=target_genre_request)
    assert target_genre_response.status_code == 200
    final_reply = target_genre_response.json()["reply"]
    
    # Verify success
    assert "Lesson generation coming soon" in final_reply
    assert "Kindergarten" in final_reply
    assert "grammar" in final_reply
    assert "action verbs" in final_reply


# ============================================================================
# IDEA GENERATION TESTS
# ============================================================================

def test_collect_idea_gen_success(client):
    """
    Test successful collection of all idea generation parameters.
    
    Flow:
    1. User: "Hello" -> AI: Greeting
    2. User: "Idea Generation" -> AI: Grade question
    3. User: "Pre-K" -> AI: Query type question
    4. User: "idea_generation" -> AI: Target genre question
    5. User: "narrative" -> AI: Target topic question
    6. User: "My Family" -> AI: Stub generation message with collected params
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
    
    # Verify AI asks the grade question with options
    assert "target grade level" in grade_question.lower()
    assert "Pre-K" in grade_question
    assert "Kindergarten" in grade_question
    assert "First Grade" in grade_question
    
    # Respond with valid grade
    grade_request = {
        "message": "Pre-K",
        "thread_id": thread_id
    }
    grade_response = client.post("/api/v1/chat/message", json=grade_request)
    assert grade_response.status_code == 200
    query_type_question = grade_response.json()["reply"]
    
    # Verify AI asks the query_type question with options
    assert "aspect of idea generation" in query_type_question.lower() or "organization" in query_type_question.lower()
    assert "idea generation" in query_type_question
    assert "organization" in query_type_question
    assert "genre elements" in query_type_question
    assert "brainstorming" in query_type_question
    assert "general" in query_type_question
    assert "__CLARIFY__" not in query_type_question
    
    # Respond with valid query type
    query_type_request = {
        "message": "idea generation",
        "thread_id": thread_id
    }
    query_type_response = client.post("/api/v1/chat/message", json=query_type_request)
    assert query_type_response.status_code == 200
    target_genre_question = query_type_response.json()["reply"]
    
    # Verify AI asks the target_genre question with options
    assert "genre" in target_genre_question.lower()
    assert "narrative" in target_genre_question
    assert "informational" in target_genre_question
    assert "opinion" in target_genre_question
    assert "personal narrative" in target_genre_question
    assert "compare contrast" in target_genre_question
    assert "__CLARIFY__" not in target_genre_question
    
    # Respond with target genre
    target_genre_request = {
        "message": "narrative",
        "thread_id": thread_id
    }
    target_genre_response = client.post("/api/v1/chat/message", json=target_genre_request)
    assert target_genre_response.status_code == 200
    target_topic_question = target_genre_response.json()["reply"]
    
    # Verify AI asks the target_topic question
    assert "topic" in target_topic_question.lower()
    
    # Respond with target topic
    target_topic_request = {
        "message": "My Family",
        "thread_id": thread_id
    }
    target_topic_response = client.post("/api/v1/chat/message", json=target_topic_request)
    assert target_topic_response.status_code == 200
    final_reply = target_topic_response.json()["reply"]
    
    # Verify we get the stub generation message with collected params
    assert "Lesson generation coming soon" in final_reply
    assert "Pre-K" in final_reply
    assert "idea generation" in final_reply
    assert "narrative" in final_reply
    assert "My Family" in final_reply


def test_collect_idea_gen_query_type_invalid(client):
    """
    Test handling of invalid choice for idea generation query_type parameter.
    
    Flow:
    1. User: "Hello" -> AI: Greeting
    2. User: "Idea Generation" -> AI: Grade question
    3. User: "Kindergarten" -> AI: Query type question
    4. User: "creative writing" -> AI: Error message + re-ask query type question
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
    
    # Respond with valid grade
    grade_request = {
        "message": "Kindergarten",
        "thread_id": thread_id
    }
    grade_response = client.post("/api/v1/chat/message", json=grade_request)
    assert grade_response.status_code == 200
    query_type_question = grade_response.json()["reply"]
    
    # Verify query type question
    assert "aspect of idea generation" in query_type_question.lower() or "organization" in query_type_question.lower()
    
    # Respond with invalid query type
    invalid_request = {
        "message": "creative writing",
        "thread_id": thread_id
    }
    invalid_response = client.post("/api/v1/chat/message", json=invalid_request)
    assert invalid_response.status_code == 200
    error_reply = invalid_response.json()["reply"]
    
    # Verify error message and re-asking
    assert "Sorry" in error_reply
    assert "didn't quite understand" in error_reply or "try again" in error_reply
    assert "aspect of idea generation" in error_reply.lower() or "organization" in error_reply.lower()


def test_collect_idea_gen_target_genre_invalid(client):
    """
    Test handling of invalid choice for idea generation target_genre parameter (Literal).
    
    Flow:
    1. User: "Hello" -> AI: Greeting
    2. User: "Idea Generation" -> AI: Grade question
    3. User: "First Grade" -> AI: Query type question
    4. User: "brainstorming" -> AI: Target genre question
    5. User: "poetry" -> AI: Error message + re-ask target genre question
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
    
    # Respond with valid grade
    grade_request = {
        "message": "First Grade",
        "thread_id": thread_id
    }
    grade_response = client.post("/api/v1/chat/message", json=grade_request)
    assert grade_response.status_code == 200
    
    # Respond with valid query type
    query_type_request = {
        "message": "brainstorming",
        "thread_id": thread_id
    }
    query_type_response = client.post("/api/v1/chat/message", json=query_type_request)
    assert query_type_response.status_code == 200
    target_genre_question = query_type_response.json()["reply"]
    
    # Verify target genre question
    assert "genre" in target_genre_question.lower()
    
    # Respond with invalid genre
    invalid_request = {
        "message": "poetry",
        "thread_id": thread_id
    }
    invalid_response = client.post("/api/v1/chat/message", json=invalid_request)
    assert invalid_response.status_code == 200
    error_reply = invalid_response.json()["reply"]
    
    # Verify error message and re-asking
    assert "Sorry" in error_reply
    assert "didn't quite understand" in error_reply or "try again" in error_reply
    assert "genre" in error_reply.lower()


def test_collect_idea_gen_invalid_then_valid(client):
    """
    Test recovery from invalid inputs for idea generation task.
    
    Flow:
    1. User: "Hello" -> AI: Greeting
    2. User: "Idea Generation" -> AI: Grade question
    3. User: "Kindergarten" -> AI: Query type question
    4. User: "handwriting practice" -> AI: Error + re-ask
    5. User: "organization" -> AI: Target genre question
    6. User: "poetry" -> AI: Error + re-ask
    7. User: "informational" -> AI: Target topic question
    8. User: "Community Helpers" -> AI: Stub generation
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
    
    # Respond with valid grade
    grade_request = {
        "message": "Kindergarten",
        "thread_id": thread_id
    }
    grade_response = client.post("/api/v1/chat/message", json=grade_request)
    assert grade_response.status_code == 200
    
    # Respond with invalid query type
    invalid_query_request = {
        "message": "handwriting practice",
        "thread_id": thread_id
    }
    invalid_query_response = client.post("/api/v1/chat/message", json=invalid_query_request)
    assert invalid_query_response.status_code == 200
    error_reply = invalid_query_response.json()["reply"]
    
    # Verify error message
    assert "Sorry" in error_reply
    
    # Respond with valid query type
    valid_query_request = {
        "message": "organization",
        "thread_id": thread_id
    }
    valid_query_response = client.post("/api/v1/chat/message", json=valid_query_request)
    assert valid_query_response.status_code == 200
    
    # Respond with invalid genre
    invalid_genre_request = {
        "message": "poetry",
        "thread_id": thread_id
    }
    invalid_genre_response = client.post("/api/v1/chat/message", json=invalid_genre_request)
    assert invalid_genre_response.status_code == 200
    error_reply2 = invalid_genre_response.json()["reply"]
    
    # Verify error message
    assert "Sorry" in error_reply2
    
    # Respond with valid genre
    valid_genre_request = {
        "message": "informational",
        "thread_id": thread_id
    }
    valid_genre_response = client.post("/api/v1/chat/message", json=valid_genre_request)
    assert valid_genre_response.status_code == 200
    
    # Respond with target topic
    target_topic_request = {
        "message": "Community Helpers",
        "thread_id": thread_id
    }
    target_topic_response = client.post("/api/v1/chat/message", json=target_topic_request)
    assert target_topic_response.status_code == 200
    final_reply = target_topic_response.json()["reply"]
    
    # Verify success
    assert "Lesson generation coming soon" in final_reply
    assert "Kindergarten" in final_reply
    assert "organization" in final_reply
    assert "informational" in final_reply
    assert "Community Helpers" in final_reply
