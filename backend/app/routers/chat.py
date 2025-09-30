"""
Chat router for the FastAPI application.
Contains HTTP endpoints for testing lesson planner graph functionality.
"""
import uuid
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel


router = APIRouter(prefix="/chat", tags=["Chat"])


class LessonPlanResponse(BaseModel):
    """Response model for lesson plan generation."""
    thread_id: str
    topic: str
    lesson_plan: str
    status: str


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
        
        # Test the graph with the handcoded topic
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
