"""
Chat service module containing the core chatbot logic.
This service encapsulates LangChain LCEL chain integration and message handling.
"""

from typing import Dict, Any
import asyncio
import uuid

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain_core.output_parsers import StrOutputParser
from app.config import settings


class ChatService:
    """
    Service class that encapsulates the core chatbot logic using LangChain LCEL.
    This service will be dependency-injected into the API router.
    """
    
    def __init__(self):
        """
        Initialize the ChatService with LangChain LCEL chain.
        """
        # Initialize ChatOpenAI model with API key from settings
        model = ChatOpenAI(
            api_key=settings.openai_api_key.get_secret_value() if settings.openai_api_key else None
        )
        
        # Create a simple ChatPromptTemplate
        prompt = ChatPromptTemplate.from_messages([
            ("system", "You are a helpful assistant."),
            ("user", "{input}")
        ])
        
        # Define the LCEL chain
        self.chain = prompt | model | StrOutputParser()
    
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
        Main async method to handle incoming messages and generate responses.
        
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
        
        # Invoke the LCEL chain with the user message
        reply = await self.chain.ainvoke({"input": user_message})
        
        response = {
            "reply": reply,
            "thread_id": thread_id
        }
        
        return response