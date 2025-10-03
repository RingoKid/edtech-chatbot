"""
Chat router for the FastAPI application.
Contains HTTP endpoints for chat functionality using LangGraph.
"""
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.service.chat_service import ChatService
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse


router = APIRouter(prefix="/chat", tags=["Chat"])

# Initialize the chat service
chat_service = ChatService()


class LessonPlanResponse(BaseModel):
    """Response model for lesson plan generation."""
    thread_id: str
    topic: str
    lesson_plan: str
    status: str


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(request: ChatMessageRequest):
    """
    Send a message to the chatbot and receive a response from the LangGraph.

    Args:
        request: ChatMessageRequest containing the message and optional thread_id

    Returns:
        ChatMessageResponse: The AI's response and thread_id
    """
    try:
        # Use a default user_id for now (can be replaced with auth later)
        user_id = "default_user"

        # Handle the message using the chat service
        result = await chat_service.handle_message(
            user_message=request.message,
            user_id=user_id,
            thread_id=request.thread_id
        )

        return ChatMessageResponse(
            thread_id=result["thread_id"],
            reply=result["reply"]
        )

    except Exception as e:
        print(f"Error handling chat message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )


@router.get("/test-lesson-planner")
async def test_lesson_planner():
    """
    HTTP endpoint to test the lesson planner graph with a hardcoded handwriting topic.
    
    Returns:
        LessonPlanResponse: The generated lesson plan for handwriting
    """
    # Generate a unique thread_id for LangSmith tracing
    thread_id = str(uuid.uuid4())
    config = {"configurable": {"thread_id": thread_id}}
    
    # Hardcoded topic for testing
    hardcoded_topic = "handwriting"
    
    try:
        # Import the lesson planner app here to catch import errors
        from app.graph.lesson_planner import lesson_planner_app
        
        # Test the graph with the hardcoded topic
        topic_input = {"topic": hardcoded_topic}
        
        # Invoke the graph (not streaming for HTTP response)
        result = lesson_planner_app.invoke(topic_input, config=config)
        
        # Extract the lesson plan from the result
        lesson_plan_content = result.get("lesson_plan", "No lesson plan generated")
        
        return LessonPlanResponse(
            thread_id=thread_id,
            topic=hardcoded_topic,
            lesson_plan=lesson_plan_content,
            status="success"
        )
        
    except ImportError as import_error:
        print(f"Import error for thread {thread_id}: {str(import_error)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to import lesson planner: {str(import_error)}"
        )
    except Exception as e:
        print(f"Error generating lesson plan for thread {thread_id}: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to generate lesson plan: {str(e)}"
        )
