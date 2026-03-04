"""
Chat service module containing the core chatbot logic.
This service encapsulates LangGraph integration and message handling.
"""

from typing import Dict, Any, List, Optional
import uuid
import json

from fastapi import WebSocket, WebSocketDisconnect
from app.graph.graph import create_graph
from langchain_core.messages import HumanMessage
from app.schemas.chat import ChatMessageRequest, ChatMessageResponse
from app.schemas.chat_history import MessageItem
from app.services.chat_history_service import get_chat_history_service
from app.services.feedback_service import get_feedback_service


class ChatService:
    """
    Service class that encapsulates the core chatbot logic using LangGraph.
    This service will be dependency-injected into the API router.
    """

    def __init__(self):
        """
        Initialize the ChatService with LangGraph.
        Uses lazy initialization for the graph since create_graph() is async.
        """
        self._graph = None

    async def _get_graph(self):
        """
        Lazy initialization of the graph.
        Creates the graph on first use in an async context.
        """
        if self._graph is None:
            self._graph = await create_graph()
        return self._graph

    def create_new_thread(self) -> str:
        """
        Create a new thread ID.

        Returns:
            str: A new UUID-based thread ID
        """
        return str(uuid.uuid4())

    async def init_chat(self, user_id: str) -> ChatMessageResponse:
        """
        Initialize a new chat session.
        Creates a new thread and returns a static greeting.
        The routing agent will be invoked on the first user message.

        Args:
            user_id (str): The user identifier

        Returns:
            ChatMessageResponse: The greeting message and new thread_id
        """
        # Create a new thread (plain UUID)
        thread_id = self.create_new_thread()

        # Create conversation record in DynamoDB
        chat_history_service = get_chat_history_service()
        await chat_history_service.create_conversation(user_id, thread_id)

        # Return static greeting - the routing agent will handle the conversation
        # when the user sends their first message. This avoids the double-greeting
        # issue where init invokes the agent and then the first message invokes it again.
        reply = (
            "Hello! I'm your lesson planning assistant. "
            "I can help you with **Handwriting**, **Vocabulary**, or **Idea Generation** lessons. "
            "What would you like to work on today?"
        )

        return ChatMessageResponse(
            thread_id=thread_id,
            reply=reply
        )

    async def process_chat_request(
        self,
        request: ChatMessageRequest,
        user_id: str
    ) -> ChatMessageResponse:
        """
        Process a chat message request and return a response.
        This method encapsulates all business logic for handling chat requests.

        Args:
            request (ChatMessageRequest): The chat message request
            user_id (str): The authenticated user's ID

        Returns:
            ChatMessageResponse: The AI's response and thread_id

        Raises:
            Exception: If there's an error processing the message
        """
        # Handle the message using the chat service
        result = await self.handle_message(
            user_message=request.message,
            user_id=user_id,
            thread_id=request.thread_id
        )

        return ChatMessageResponse(
            thread_id=result["thread_id"],
            reply=result["reply"],
        )

    async def handle_message(
        self,
        user_message: str,
        user_id: str,
        thread_id: str | None = None
    ) -> Dict[str, Any]:
        """
        Main async method to handle incoming messages and generate responses using the graph.

        Args:
            user_message (str): The message received from the user
            user_id (str): The user identifier
            thread_id (str | None): Optional unique identifier for the conversation thread

        Returns:
            Dict[str, Any]: Dictionary containing the chatbot's response and thread_id
        """
        # Get the graph instance (lazy initialization)
        graph = await self._get_graph()
        chat_history_service = get_chat_history_service()

        # Handle thread_id logic
        is_new_thread = thread_id is None
        if is_new_thread:
            thread_id = self.create_new_thread()
            # Create conversation record for new thread
            await chat_history_service.create_conversation(user_id, thread_id)

        # Create config with thread_id for graph execution
        config = {"configurable": {"thread_id": thread_id}}

        # Check if this thread has an existing state (interrupted at greeting_node)
        current_state = await graph.aget_state(config)

        if current_state and current_state.next:
            # Thread exists and is interrupted - resume with user's message by updating state
            await graph.aupdate_state(
                config,
                {"messages": [HumanMessage(content=user_message)]}
            )
            # Continue from the interrupted point with None input
            result = await graph.ainvoke(None, config=config)
        else:
            # New thread or completed thread - start fresh
            input_state = {
                "messages": [HumanMessage(content=user_message)]
            }
            result = await graph.ainvoke(input_state, config=config)

        # Extract the AI response from the result
        messages = result.get("messages", [])
        if messages:
            # Get the last message which should be the AI's response
            last_message = messages[-1]
            reply = last_message.content
        else:
            reply = "I'm sorry, I couldn't generate a response."

        # Update conversation metadata
        # Update title if task_type was set (v2 architecture)
        task_type = result.get("task_type")
        if task_type:
            # Map task_type to display name
            task_display_names = {
                "handwriting": "Handwriting",
                "vocabulary": "Vocabulary",
                "idea_generation": "Idea Generation",
            }
            title = task_display_names.get(task_type, task_type.title())
            await chat_history_service.update_title(user_id, thread_id, title)

        # Update last_message_preview with the AI's response
        await chat_history_service.update_preview(user_id, thread_id, reply)

        # Persist feedback if collected
        feedback_data = result.get("feedback_data")
        if feedback_data:
            feedback_service = get_feedback_service()
            await feedback_service.save_feedback(
                thread_id=thread_id,
                user_id=user_id,
                task_type=result.get("task_type", "unknown"),
                category=feedback_data["category"],
                rating=feedback_data.get("rating"),
                text=feedback_data["text"],
            )

        # Replace IMAGE_N tokens with S3 URLs if available
        image_urls = result.get("image_urls")
        if image_urls:
            for i, url in enumerate(image_urls, start=1):
                reply = reply.replace(f"IMAGE_{i}", url)

        return {
            "reply": reply,
            "thread_id": thread_id,
        }

    async def get_conversation_messages(
        self,
        thread_id: str
    ) -> List[MessageItem]:
        """
        Get all messages for a conversation from the checkpointer.

        Args:
            thread_id: The thread identifier

        Returns:
            List of MessageItem objects
        """
        graph = await self._get_graph()
        config = {"configurable": {"thread_id": thread_id}}

        state = await graph.aget_state(config)

        if state is None or not state.values:
            return []

        messages = state.values.get("messages", [])
        result = []

        for msg in messages:
            # Determine role based on message type
            if hasattr(msg, 'type'):
                if msg.type == 'human':
                    role = 'user'
                elif msg.type == 'ai':
                    role = 'assistant'
                else:
                    role = msg.type
            else:
                role = 'unknown'

            result.append(MessageItem(
                role=role,
                content=msg.content if hasattr(msg, 'content') else str(msg),
                timestamp=None  # Checkpointer doesn't store timestamps per message
            ))

        return result

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

                # Get the graph instance (lazy initialization)
                graph = await self._get_graph()

                # Stream events from the graph
                async for event in graph.astream_events(input_state, config=config, version="v1"):
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
