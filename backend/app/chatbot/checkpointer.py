"""
Centralized Checkpointer for Educational Chatbot.
Single source of truth for conversation state persistence across all graphs.
Uses AsyncSqliteSaver for persistent storage with proper lifecycle management.
"""
import os
import asyncio
from pathlib import Path
from langgraph.checkpoint.sqlite.aio import AsyncSqliteSaver
from app.config import settings

class CheckpointerManager:
    """
    Singleton manager for conversation state persistence.
    Ensures all graphs (routing, handwriting, vocabulary, ideas) use the same checkpointer.
    Uses AsyncSqliteSaver with persistent file storage.
    """

    _instance = None
    _checkpointer = None
    _context_manager = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(CheckpointerManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        """Initialize the checkpointer only once."""
        if self._checkpointer is None:
            # Note: Actual initialization happens in async_init()
            # which must be called from an async context
            pass

    async def async_init(self):
        """
        Async initialization of the checkpointer.
        Must be called once at application startup.
        """
        if self._checkpointer is not None:
            return  # Already initialized

        # Create checkpoints directory if it doesn't exist
        checkpoint_dir = Path(__file__).parent.parent.parent / "checkpoints"
        checkpoint_dir.mkdir(exist_ok=True)

        # Database file path
        db_path = checkpoint_dir / "conversations.db"

        print("🗄️ Initializing ASYNC SQLITE checkpointer for persistent conversation storage")
        print(f"💾 Database path: {db_path}")

        # Create AsyncSqliteSaver context manager
        self._context_manager = AsyncSqliteSaver.from_conn_string(str(db_path))

        # Enter the context manager and keep it alive
        self._checkpointer = await self._context_manager.__aenter__()

        print("✅ Shared AsyncSqliteSaver checkpointer initialized successfully")
        print("💾 Conversation history will persist across server restarts")
        print("📁 Database: backend/checkpoints/conversations.db")

    async def async_close(self):
        """
        Close the checkpointer properly.
        Should be called at application shutdown.
        """
        if self._context_manager and self._checkpointer:
            print("🔄 Closing AsyncSqliteSaver checkpointer...")
            await self._context_manager.__aexit__(None, None, None)
            self._checkpointer = None
            self._context_manager = None
            print("✅ Checkpointer closed")

    def get_checkpointer(self) -> AsyncSqliteSaver:
        """
        Get the shared checkpointer instance.

        Returns:
            AsyncSqliteSaver: The shared async checkpointer for all graphs

        Raises:
            RuntimeError: If checkpointer hasn't been initialized yet
        """
        if self._checkpointer is None:
            raise RuntimeError(
                "Checkpointer not initialized! Call await checkpointer_manager.async_init() first."
            )
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


def get_shared_checkpointer() -> AsyncSqliteSaver:
    """
    Get the shared checkpointer for all graphs.

    Usage:
        from app.chatbot.checkpointer import get_shared_checkpointer

        checkpointer = get_shared_checkpointer()
        graph = graph_builder.compile(checkpointer=checkpointer)

    Returns:
        AsyncSqliteSaver: The shared async checkpointer instance with persistent storage
    """
    return checkpointer_manager.get_checkpointer()