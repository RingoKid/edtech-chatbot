"""
Chat history service for managing conversation records in DynamoDB.
Handles user-thread mappings for the chat history API.
"""

import asyncio
from datetime import datetime, timezone
from typing import List, Optional
from boto3.dynamodb.conditions import Key

from app.models import Conversation
from app.database import get_db


# Task name to display title mapping
TASK_NAME_TO_TITLE = {
    "Handwriting": "Handwriting Practice",
    "Vocabulary": "Vocabulary Learning",
    "Idea Generation": "Idea Generation",
}


class ChatHistoryService:
    """Service for managing conversation records in DynamoDB."""

    def __init__(self, table=None):
        """
        Initialize the service.

        Args:
            table: Optional DynamoDB table resource. If not provided,
                   uses the default table from settings.
        """
        if table is not None:
            self.table = table
        else:
            self.table = get_db()

    def _make_pk(self, user_id: str) -> str:
        """Generate partition key for user."""
        return f"USER#{user_id}"

    def _make_sk(self, thread_id: str) -> str:
        """Generate sort key for thread."""
        return f"THREAD#{thread_id}"

    def _now_iso(self) -> str:
        """Get current timestamp in ISO format."""
        return datetime.now(timezone.utc).isoformat()

    async def create_conversation(self, user_id: str, thread_id: str) -> Conversation:
        """
        Create a new conversation record for a user.

        Args:
            user_id: The user identifier
            thread_id: The thread identifier

        Returns:
            The created Conversation object
        """
        now = self._now_iso()
        pk = self._make_pk(user_id)
        sk = self._make_sk(thread_id)

        item = {
            'PK': pk,
            'SK': sk,
            'type': 'Conversation',
            'thread_id': thread_id,
            'user_id': user_id,
            'title': 'New Conversation',
            'last_message_preview': None,
            'created_at': now,
            'updated_at': now,
        }

        await asyncio.to_thread(self.table.put_item, Item=item)

        return Conversation(**item)

    async def get_conversation(self, user_id: str, thread_id: str) -> Optional[Conversation]:
        """
        Get a single conversation by user_id and thread_id.

        Args:
            user_id: The user identifier
            thread_id: The thread identifier

        Returns:
            Conversation object if found, None otherwise
        """
        pk = self._make_pk(user_id)
        sk = self._make_sk(thread_id)

        response = await asyncio.to_thread(self.table.get_item, Key={'PK': pk, 'SK': sk})
        item = response.get('Item')

        if item is None:
            return None

        return Conversation(**item)

    async def get_user_conversations(self, user_id: str) -> List[Conversation]:
        """
        Get all conversations for a user.

        Args:
            user_id: The user identifier

        Returns:
            List of Conversation objects, ordered by updated_at descending
        """
        pk = self._make_pk(user_id)

        response = await asyncio.to_thread(
            self.table.query,
            KeyConditionExpression=Key('PK').eq(pk) & Key('SK').begins_with('THREAD#')
        )

        conversations = [Conversation(**item) for item in response.get('Items', [])]

        # Sort by updated_at descending (most recent first)
        conversations.sort(key=lambda c: c.updated_at, reverse=True)

        return conversations

    async def update_title(self, user_id: str, thread_id: str, task_name: str) -> None:
        """
        Update conversation title based on task name.

        Args:
            user_id: The user identifier
            thread_id: The thread identifier
            task_name: The task name from GraphState (e.g., "Handwriting", "Vocabulary")
        """
        pk = self._make_pk(user_id)
        sk = self._make_sk(thread_id)

        # Map task name to display title
        title = TASK_NAME_TO_TITLE.get(task_name, task_name)

        await asyncio.to_thread(
            self.table.update_item,
            Key={'PK': pk, 'SK': sk},
            UpdateExpression='SET title = :title, updated_at = :updated_at',
            ExpressionAttributeValues={
                ':title': title,
                ':updated_at': self._now_iso(),
            }
        )

    async def update_preview(self, user_id: str, thread_id: str, message: str) -> None:
        """
        Update last_message_preview for a conversation.

        Args:
            user_id: The user identifier
            thread_id: The thread identifier
            message: The message content (will be truncated to 100 chars)
        """
        pk = self._make_pk(user_id)
        sk = self._make_sk(thread_id)

        # Truncate to 100 characters
        preview = message[:100] if len(message) > 100 else message

        await asyncio.to_thread(
            self.table.update_item,
            Key={'PK': pk, 'SK': sk},
            UpdateExpression='SET last_message_preview = :preview, updated_at = :updated_at',
            ExpressionAttributeValues={
                ':preview': preview,
                ':updated_at': self._now_iso(),
            }
        )

    async def verify_ownership(self, user_id: str, thread_id: str) -> bool:
        """
        Verify that a user owns a specific thread.

        Args:
            user_id: The user identifier
            thread_id: The thread identifier

        Returns:
            True if user owns the thread, False otherwise
        """
        conversation = await self.get_conversation(user_id, thread_id)
        return conversation is not None


# Singleton instance for dependency injection
_chat_history_service: Optional[ChatHistoryService] = None


def get_chat_history_service() -> ChatHistoryService:
    """Get or create the ChatHistoryService singleton."""
    global _chat_history_service
    if _chat_history_service is None:
        _chat_history_service = ChatHistoryService()
    return _chat_history_service
