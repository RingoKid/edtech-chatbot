"""
Chat router for the FastAPI application.
Contains HTTP endpoints for chat functionality using LangGraph.
"""
from fastapi import APIRouter, HTTPException, Depends, WebSocket
from fastapi.responses import JSONResponse

from app.services.chat_service import ChatService
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse, ChatHistoryResponse


router = APIRouter(prefix="/chat2", tags=["Chat2"])


def get_chat_service() -> ChatService:
    """
    Dependency function to get ChatService instance.
    This creates a new instance for each request.
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


@router.get("/history/{thread_id}", response_model=ChatHistoryResponse)
async def get_chat_history(
    thread_id: str,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    Retrieve full conversation history for a specific thread.

    This endpoint returns all messages in a conversation thread, along with metadata
    like bot type, target letters, and grade level. The frontend can use this data
    to generate a downloadable PDF or display conversation history.

    **Example Usage:**
    ```
    GET /api/v1/chat2/history/default_user_abc12345
    ```

    **Response includes:**
    - `thread_id`: The conversation thread identifier
    - `message_count`: Total number of messages in the conversation
    - `created_at`: Timestamp of the first message
    - `last_updated`: Timestamp of the last message
    - `metadata`: Conversation context (bot_type, target_letters, grade_level, intent)
    - `messages`: Array of all messages with role (user/assistant), content, and timestamp

    Args:
        thread_id: The unique conversation thread identifier
        chat_service: Injected ChatService instance

    Returns:
        ChatHistoryResponse: Complete conversation history with metadata

    Raises:
        404: Thread ID not found or no messages in thread
        500: Server error retrieving history
    """
    try:
        return await chat_service.get_chat_history(thread_id)

    except HTTPException:
        # Re-raise HTTP exceptions (404, 500) from service layer
        raise
    except Exception as e:
        print(f"Error retrieving chat history: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Unexpected error retrieving chat history: {str(e)}"
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
        "endpoint": "/api/v1/chat2/ws/message",
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
            "local": "ws://localhost:8000/api/v1/chat2/ws/message",
            "production": "wss://your-domain.com/api/v1/chat2/ws/message"
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


@router.websocket("/ws/audio")
async def websocket_audio(
    websocket: WebSocket,
    chat_service: ChatService = Depends(get_chat_service)
):
    """
    WebSocket endpoint for voice input (audio streaming + transcription).

    **Protocol:**
    - Client sends binary audio frames (WebM/Opus format recommended)
    - Client sends control messages: {"type": "audio_end", "thread_id": "..."}
    - Server sends: {"type": "transcript", "text": "..."} after transcription
    - Server sends: {"type": "response", "text": "...", "thread_id": "..."} with LLM response
    - Server sends: {"type": "error", "message": "..."} on errors

    **Audio Format Recommendations:**
    - Codec: WebM with Opus audio
    - Sample Rate: 16kHz (optimal for Whisper)
    - Channels: Mono (1 channel)
    - Bitrate: 16-32 kbps

    **Example Usage (JavaScript):**
    ```javascript
    const ws = new WebSocket('ws://localhost:8000/api/v1/chat2/ws/audio');
    const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
    });

    mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
            ws.send(event.data);  // Send binary audio
        }
    };

    // When recording stops
    mediaRecorder.onstop = () => {
        ws.send(JSON.stringify({
            type: 'audio_end',
            thread_id: currentThreadId
        }));
    };

    ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'transcript') {
            console.log('Transcribed:', data.text);
        } else if (data.type === 'response') {
            console.log('AI Response:', data.text);
        }
    };
    ```

    Args:
        websocket: The WebSocket connection instance
        chat_service: Injected ChatService instance
    """
    await chat_service.handle_audio_websocket_connection(websocket)