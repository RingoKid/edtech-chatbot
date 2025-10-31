"""
Centralized Checkpointer for Educational Chatbot.
Single source of truth for conversation state persistence across all graphs.
Uses SqliteSaver for persistent storage like LangGraph Studio.
"""
import os
from pathlib import Path
from langgraph.checkpoint.sqlite import SqliteSaver
from app.config import settings

class CheckpointerManager:
    """
    Singleton manager for conversation state persistence.
    Ensures all graphs (routing, handwriting, vocabulary, ideas) use the same checkpointer.
    Uses SqliteSaver with persistent file storage (same as LangGraph Studio).
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
        # Using SqliteSaver for persistent conversation storage (same as LangGraph Studio)

        # Create checkpoints directory if it doesn't exist
        checkpoint_dir = Path(__file__).parent.parent.parent / "checkpoints"
        checkpoint_dir.mkdir(exist_ok=True)

        # Database file path
        db_path = checkpoint_dir / "conversations.db"

        print("🗄️ Initializing SQLITE checkpointer for persistent conversation storage")
        print(f"💾 Database path: {db_path}")
        print("✅ Conversations will persist across server restarts (same as LangGraph Studio)")

        # Create SqliteSaver with connection string
        # Using synchronous SqliteSaver (same pattern as LangGraph Studio)
        self._checkpointer = SqliteSaver.from_conn_string(str(db_path))

        print("✅ Shared SqliteSaver checkpointer initialized successfully")
        print("💾 All conversation state will be persisted to SQLite database")

    def get_checkpointer(self) -> SqliteSaver:
        """
        Get the shared checkpointer instance.

        Returns:
            MemorySaver: The shared checkpointer for all graphs
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
        SqliteSaver: The shared checkpointer instance with persistent storage
    """
    return checkpointer_manager.get_checkpointer()