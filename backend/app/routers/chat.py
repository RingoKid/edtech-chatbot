"""
Chat router for the FastAPI application.
Contains endpoints for chat functionality and conversation management.
"""
from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional

router = APIRouter()


class MessageIn(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class MessageOut(BaseModel):
    reply: str
    conversation_id: Optional[str] = None


@router.get("/chat", tags=["Chat"])
def get_chat_status():
    """
    Placeholder endpoint for chat functionality.
    """
    return {"router": "chat", "status": "active", "message": "Chat router is working"}



@router.post("/message", response_model=MessageOut, tags=["Chat"])
def post_message(payload: MessageIn):
    """
    Simple demo endpoint that returns a canned reply to the provided message.
    This is a placeholder for the real chat/message handling logic.
    """
    user_text = payload.message or ""
    # Very simple canned reply logic for demo
    if 'phonics' in user_text.lower():
        reply = "(Demo) Try multi-sensory phonics activities — sand writing, letter tiles, and songs."
    elif 'behavior' in user_text.lower():
        reply = "(Demo) Consider clear expectations, routines, and positive reinforcement."
    else:
        reply = "(Demo) Thanks for your question. This is a demo reply from the chat endpoint."

    return {"reply": reply, "conversation_id": payload.conversation_id}
