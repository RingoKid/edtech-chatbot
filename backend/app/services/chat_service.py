"""
Chat service module containing the core chatbot logic.
This service encapsulates LangGraph integration and message handling.
"""

from typing import Dict, Any
import uuid
import json

from fastapi import WebSocket, WebSocketDisconnect
from app.chatbot.studio.studio_router import studio_router
from langchain_core.messages import HumanMessage
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse


class ChatService:
    """
    Service class that encapsulates the core chatbot logic using LangGraph.
    This service will be dependency-injected into the API router.
    """

    def __init__(self):
        """
        Initialize the ChatService with the complete routing graph.
        This graph routes to specialized bots: handwriting, vocabulary, ideas, and general.
        """
        self.graph = studio_router

    def create_new_thread(self, user_id: str) -> str:
        """
        Create a new thread ID for a user conversation.

        Args:
            user_id (str): The user identifier

        Returns:
            str: A new thread ID
        """
        # Generate a new thread ID combining user_id and UUID
        thread_id = f"{user_id}_{uuid.uuid4().hex[:8]}"
        return thread_id

    async def process_chat_request(self, request: ChatMessageRequest) -> ChatMessageResponse:
        """
        Process a chat message request and return a response.
        This method encapsulates all business logic for handling chat requests.

        Args:
            request (ChatMessageRequest): The chat message request

        Returns:
            ChatMessageResponse: The AI's response and thread_id

        Raises:
            Exception: If there's an error processing the message
        """
        # Use a default user_id for now (can be replaced with auth later)
        user_id = "default_user"

        # Handle the message using the chat service
        result = await self.handle_message(
            user_message=request.message,
            user_id=user_id,
            thread_id=request.thread_id
        )

        return ChatMessageResponse(
            thread_id=result["thread_id"],
            reply=result["reply"]
        )

    async def handle_message(self, user_message: str, user_id: str, thread_id: str | None = None) -> Dict[str, Any]:
        """
        Main async method to handle incoming messages and generate responses using the graph.

        Args:
            user_message (str): The message received from the user
            user_id (str): The user identifier
            thread_id (str | None): Optional unique identifier for the conversation thread

        Returns:
            Dict[str, Any]: Dictionary containing the chatbot's response and thread_id
        """
        # Handle thread_id logic
        if thread_id is None:
            thread_id = self.create_new_thread(user_id)

        # Create config with thread_id for graph execution
        config = {"configurable": {"thread_id": thread_id}}

        # Create the input state with the user's message
        input_state = {
            "messages": [HumanMessage(content=user_message)]
        }

        # Invoke the graph with the user message
        result = await self.graph.ainvoke(input_state, config=config)

        # Extract the AI response from the result
        messages = result.get("messages", [])
        if messages:
            # Get the last message which should be the AI's response
            last_message = messages[-1]
            reply = last_message.content
        else:
            reply = "I'm sorry, I couldn't generate a response."

        response = {
            "reply": reply,
            "thread_id": thread_id
        }

        return response

    async def handle_websocket_connection(self, websocket: WebSocket):
        """
        Handle WebSocket connection for real-time chat with streaming.
        Continuously receives JSON messages from the client, validates them,
        and streams token chunks from the language model directly over the WebSocket.

        Args:
            websocket (WebSocket): The WebSocket connection instance from FastAPI
        """
        await websocket.accept()

        try:
            while True:
                # Receive JSON message from the client
                data = await websocket.receive_text()

                # Parse and validate the message with ChatMessageRequest
                message_data = json.loads(data)
                request = ChatMessageRequest(**message_data)

                # Use a default user_id for now (can be replaced with auth later)
                user_id = "default_user"

                # Handle thread_id logic
                thread_id = request.thread_id
                if thread_id is None:
                    thread_id = self.create_new_thread(user_id)

                # Create config with thread_id for graph execution
                config = {"configurable": {"thread_id": thread_id}}

                # Create the input state with the user's message
                input_state = {
                    "messages": [HumanMessage(content=request.message)]
                }

                # Stream events from the graph
                async for event in self.graph.astream_events(input_state, config=config, version="v1"):
                    # Filter for chat model stream events
                    if event["event"] == "on_chat_model_stream":
                        ## Extract the content chunk from the event
                        chunk_content = event["data"]["chunk"].content

                        # Only send non-empty chunks
                        if chunk_content:
                            # Construct a ChatMessageResponse with the chunk
                            response = ChatMessageResponse(
                                thread_id=thread_id,
                                reply=chunk_content
                            )

                            # Send the chunk as JSON over the WebSocket
                            await websocket.send_text(response.model_dump_json())

        except WebSocketDisconnect:
            print("WebSocket client disconnected")
        except Exception as e:
            print(f"Error in WebSocket connection: {str(e)}")
            await websocket.close()