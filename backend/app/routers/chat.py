"""
Chat router for the FastAPI application.
Contains HTTP endpoints for chat functionality using LangGraph.
"""
from functools import lru_cache
from fastapi import APIRouter, HTTPException, Depends, WebSocket
from fastapi.responses import JSONResponse

from app.service.chat_service import ChatService
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse


router = APIRouter(prefix="/chat", tags=["Chat"])


@lru_cache(maxsize=1)
def get_chat_service() -> ChatService:
    """
    Returns a singleton ChatService instance for the application lifecycle.
    Uses lru_cache to ensure only one instance is created and reused across requests.
    Can be overridden in tests via dependency injection to avoid event loop conflicts.
    """
    return ChatService()


@router.post("/message", response_model=ChatMessageResponse)
async def send_message(
    request: ChatMessageRequest,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Send a message to the chatbot and receive a response from the LangGraph.

    Args:
        request: ChatMessageRequest containing the message and optional thread_id
        chat_service: Injected ChatService instance

    Returns:
        ChatMessageResponse: The AI's response and thread_id
    """
    try:
        return await chat_service.process_chat_request(request)

    except Exception as e:
        print(f"Error handling chat message: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to process message: {str(e)}"
        )


@router.get("/ws/info", summary="WebSocket Connection Information")
async def websocket_info():
    """
    Get information about the WebSocket endpoint for real-time chat.

    **WebSocket Endpoint:** `/api/v1/chat/ws/message`

    **Protocol:** WebSocket (ws:// or wss://)

    **Connection Example (JavaScript):**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v1/chat/ws/message');

    ws.onopen = () => {
        ws.send(JSON.stringify({
            message: "Hello!",
            thread_id: "optional-thread-id"
        }));
    };

    ws.onmessage = (event) => {
        const response = JSON.parse(event.data);
        console.log(response);
    };
    ```

    **Message Format (Client → Server):**
    ```json
    {
        "message": "Your message here",
        "thread_id": "optional-thread-id-for-conversation-continuity"
    }
    ```

    **Response Format (Server → Client):**
    ```json
    {
        "response": "AI assistant response",
        "thread_id": "conversation-thread-id"
    }
    ```

    **Error Response:**
    ```json
    {
        "error": "Error message description"
    }
    ```

    Returns:
        JSON object with WebSocket endpoint details and usage examples
    """
    return JSONResponse(content={
        "endpoint": "/api/v1/chat/ws/message",
        "protocol": "WebSocket",
        "message_format": {
            "request": {
                "message": "string (required)",
                "thread_id": "string (optional)"
            },
            "response": {
                "response": "string",
                "thread_id": "string"
            },
            "error": {
                "error": "string"
            }
        },
        "example_urls": {
            "local": "ws://localhost:8000/api/v1/chat/ws/message",
            "production": "wss://your-domain.com/api/v1/chat/ws/message"
        },
        "usage": "Connect using WebSocket client and send/receive JSON messages"
    })


@router.websocket("/ws/message")
async def websocket_message(
    websocket: WebSocket,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    WebSocket endpoint for real-time chat communication.
    Accepts WebSocket connections and handles bidirectional chat messages.

    **Note:** This endpoint uses WebSocket protocol and won't appear in Swagger UI.
    Use the GET /ws/info endpoint above for connection details and examples.

    Args:
        websocket: The WebSocket connection instance
        chat_service: Injected ChatService instance
    """
    await chat_service.handle_websocket_connection(websocket)
