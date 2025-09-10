"""
Health check router for the FastAPI application.
Contains endpoints for monitoring application health and status.
"""
from fastapi import APIRouter

router = APIRouter()


@router.get("/health", tags=["Health"])
def read_health():
    """
    Health check endpoint to confirm the API is running.
    """
    return {"status": "ok"}


@router.get("/debug-test", tags=["Health"])
def debug_test():
    """
    Test endpoint for debugging - set a breakpoint here!
    """
    message = "This is a debug test endpoint"
    data = {
        "message": message,
        "timestamp": "2025-09-08",
        "debug": True
    }
    # Set a breakpoint on the next line to test debugging
    result = {"status": "debug-success", "data": data}
    return result
