"""
Chat service module containing the core chatbot logic.
This service encapsulates LangGraph integration and message handling.
"""

from typing import Dict, Any
import uuid

from app.graph.graph import graph
from langchain_core.messages import HumanMessage


class ChatService:
    """
    Service class that encapsulates the core chatbot logic using LangGraph.
    This service will be dependency-injected into the API router.
    """
    
    def __init__(self):
        """
        Initialize the ChatService with LangGraph.
        """
        self.graph = graph

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