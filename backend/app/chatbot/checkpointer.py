"""
Centralized Checkpointer for Educational Chatbot.
Single source of truth for conversation state persistence across all graphs.
"""
from langgraph.checkpoint.sqlite import SqliteSaver
from app.config import settings
import os

class CheckpointerManager:
    """
    Singleton manager for conversation state persistence.
    Ensures all graphs (routing, handwriting, vocabulary, ideas) use the same checkpointer.
    """

    _instance = None
    _checkpointer = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CheckpointerManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the checkpointer only once."""
        if self._checkpointer is None:
            self._initialize_checkpointer()

    def _initialize_checkpointer(self):
        """Create the checkpointer based on configuration."""
        # Use persistent SQLite database for production
        # Use in-memory for development/testing if specified

        if hasattr(settings, 'use_memory_checkpointer') and settings.use_memory_checkpointer:
            print("🗄️ Initializing IN-MEMORY checkpointer for development")
            self._checkpointer = SqliteSaver.from_conn_string(":memory:")
        else:
            # Use persistent SQLite database
            db_path = getattr(settings, 'checkpointer_db_path', './data/conversation_state.db')

            # Create directory if it doesn't exist
            os.makedirs(os.path.dirname(db_path), exist_ok=True)

            print(f"🗄️ Initializing PERSISTENT checkpointer at: {db_path}")
            self._checkpointer = SqliteSaver.from_conn_string(f"file:{db_path}")

        print("✅ Shared checkpointer initialized successfully")

    def get_checkpointer(self) -> SqliteSaver:
        """
        Get the shared checkpointer instance.

        Returns:
            SqliteSaver: The shared checkpointer for all graphs
        """
        return self._checkpointer

    def reset_checkpointer(self):
        """
        Reset the checkpointer (useful for testing).
        WARNING: This will clear all conversation history.
        """
        print("⚠️ Resetting checkpointer - all conversation history will be cleared")
        self._checkpointer = None
        self._initialize_checkpointer()
        print("✅ Checkpointer reset complete")


# Create singleton instance
checkpointer_manager = CheckpointerManager()


def get_shared_checkpointer() -> SqliteSaver:
    """
    Get the shared checkpointer for all graphs.

    Usage:
        from app.chatbot.checkpointer import get_shared_checkpointer

        checkpointer = get_shared_checkpointer()
        graph = graph_builder.compile(checkpointer=checkpointer)

    Returns:
        SqliteSaver: The shared checkpointer instance
    """
    return checkpointer_manager.get_checkpointer()