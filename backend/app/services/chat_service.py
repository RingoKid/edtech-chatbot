"""
Chat service module containing the core chatbot logic.
This service encapsulates LangGraph integration and message handling.

NOW WITH CONVERSATION MEMORY AND CROSS-BOT CONTEXT SHARING!
"""

from typing import Dict, Any
import uuid
import json

from fastapi import WebSocket, WebSocketDisconnect
from app.chatbot.studio.studio_router import studio_router_with_memory
from langchain_core.messages import HumanMessage
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse


class ChatService:
    """
    Service class that encapsulates the core chatbot logic using LangGraph.
    This service will be dependency-injected into the API router.

    Now uses studio_router_with_memory for full conversation history and cross-bot context.
    """

    def __init__(self):
        """
        Initialize the ChatService with the memory-enabled routing graph.
        This graph routes to specialized bots: handwriting, vocabulary, ideas, and general.

        Features:
        - Full conversation memory across turns
        - Cross-bot context sharing (handwriting → vocabulary transitions preserve context)
        - Transparent specialist handoffs
        """
        self.graph = studio_router_with_memory

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

        NOW WITH MEMORY: Checkpointer automatically manages conversation history via thread_id.

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

        # 🔍 DEBUG: Check what's in the checkpointer BEFORE invocation
        print(f"🔍 DEBUG - Thread ID: {thread_id}")
        try:
            prior_state = await self.graph.aget_state(config)
            if prior_state and prior_state.values:
                prior_messages = prior_state.values.get("messages", [])
                print(f"🔍 DEBUG - Found {len(prior_messages)} messages in checkpointer BEFORE invocation")
                for i, msg in enumerate(prior_messages):
                    msg_type = "Human" if hasattr(msg, 'type') and msg.type == "human" else "AI"
                    content_preview = msg.content[:50] if hasattr(msg, 'content') else str(msg)[:50]
                    print(f"   [{i}] {msg_type}: {content_preview}...")
            else:
                print(f"🔍 DEBUG - No prior state found (first message in thread)")
        except Exception as e:
            print(f"🔍 DEBUG - Error checking prior state: {e}")

        # Create the input state with just the new message
        # The checkpointer will automatically retrieve and append previous messages
        input_state = {
            "messages": [HumanMessage(content=user_message)],  # Just the new message
            "teacher_id": user_id,
            "session_id": thread_id,
            "original_query": user_message,
            "intent": None,
            "confidence": 0.0,
            "classification_reasoning": None,
            "target_bot": None,
            "routing_decision": None,
            "needs_specialist": False,  # Critical field for routing
            "specialist_topic": None,  # Critical field for routing
            "bot_response": None,
            "bot_type": None,
            "relevant_forms": [],
            "follow_up_questions": [],
            "processing_steps": [],
            "total_processing_time": 0.0,
            "needs_clarification": False,
            "last_error": None,
            "retry_count": 0,
            "conversation_depth": 0,  # Checkpointer will manage this
            "previous_intents": []
        }

        # Invoke the graph - checkpointer automatically handles conversation continuity
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

                # Create the input state with just the new message
                # The checkpointer will automatically retrieve and append previous messages
                input_state = {
                    "messages": [HumanMessage(content=request.message)],  # Just the new message
                    "teacher_id": user_id,
                    "session_id": thread_id,
                    "original_query": request.message,
                    "intent": None,
                    "confidence": 0.0,
                    "classification_reasoning": None,
                    "target_bot": None,
                    "routing_decision": None,
                    "needs_specialist": False,
                    "specialist_topic": None,
                    "bot_response": None,
                    "bot_type": None,
                    "relevant_forms": [],
                    "follow_up_questions": [],
                    "processing_steps": [],
                    "total_processing_time": 0.0,
                    "needs_clarification": False,
                    "last_error": None,
                    "retry_count": 0,
                    "conversation_depth": 0,  # Checkpointer will manage this
                    "previous_intents": []
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