"""
Conversation Memory Service for storing and retrieving chat history.
Uses DynamoDB to persist conversation history across sessions.
"""
from typing import List, Dict, Any, Optional
from datetime import datetime
from langchain_core.messages import HumanMessage, AIMessage, BaseMessage
from app.database import get_db


class ConversationMemory:
    """Service for managing conversation history in DynamoDB."""

    def __init__(self):
        """Initialize the conversation memory service."""
        self.table = get_db()
        print("✅ ConversationMemory service initialized")

    def _serialize_message(self, message: BaseMessage) -> Dict[str, Any]:
        """
        Convert a LangChain message to a dictionary for storage.

        Args:
            message: LangChain BaseMessage (HumanMessage or AIMessage)

        Returns:
            Dictionary representation of the message
        """
        return {
            "type": message.type,  # 'human' or 'ai'
            "content": message.content,
            "timestamp": datetime.utcnow().isoformat()
        }

    def _deserialize_message(self, message_dict: Dict[str, Any]) -> BaseMessage:
        """
        Convert a stored dictionary back to a LangChain message.

        Args:
            message_dict: Dictionary representation of a message

        Returns:
            LangChain BaseMessage (HumanMessage or AIMessage)
        """
        if message_dict["type"] == "human":
            return HumanMessage(content=message_dict["content"])
        elif message_dict["type"] == "ai":
            return AIMessage(content=message_dict["content"])
        else:
            # Default to HumanMessage for unknown types
            return HumanMessage(content=message_dict["content"])

    def save_conversation(
        self,
        session_id: str,
        teacher_id: str,
        messages: List[BaseMessage],
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Save conversation history to DynamoDB.

        Args:
            session_id: Unique session identifier
            teacher_id: Teacher's unique identifier
            messages: List of conversation messages
            metadata: Optional metadata (query_type, target_letters, etc.)

        Returns:
            True if successful, False otherwise
        """
        try:
            # Serialize messages
            serialized_messages = [self._serialize_message(msg) for msg in messages]

            # Create DynamoDB item
            item = {
                "PK": f"CONVERSATION#{teacher_id}",
                "SK": f"SESSION#{session_id}",
                "type": "conversation",
                "teacher_id": teacher_id,
                "session_id": session_id,
                "messages": serialized_messages,
                "message_count": len(serialized_messages),
                "last_updated": datetime.utcnow().isoformat(),
                "metadata": metadata or {}
            }

            # Save to DynamoDB
            self.table.put_item(Item=item)

            print(f"✅ Saved conversation for session {session_id} ({len(messages)} messages)")
            return True

        except Exception as e:
            print(f"❌ Error saving conversation: {str(e)}")
            return False

    def get_conversation(
        self,
        session_id: str,
        teacher_id: str
    ) -> Optional[List[BaseMessage]]:
        """
        Retrieve conversation history from DynamoDB.

        Args:
            session_id: Unique session identifier
            teacher_id: Teacher's unique identifier

        Returns:
            List of LangChain messages or None if not found
        """
        try:
            # Query DynamoDB
            response = self.table.get_item(
                Key={
                    "PK": f"CONVERSATION#{teacher_id}",
                    "SK": f"SESSION#{session_id}"
                }
            )

            if "Item" not in response:
                print(f"ℹ️ No conversation history found for session {session_id}")
                return None

            # Deserialize messages
            item = response["Item"]
            messages = [
                self._deserialize_message(msg_dict)
                for msg_dict in item.get("messages", [])
            ]

            print(f"✅ Retrieved conversation for session {session_id} ({len(messages)} messages)")
            return messages

        except Exception as e:
            print(f"❌ Error retrieving conversation: {str(e)}")
            return None

    def get_conversation_with_metadata(
        self,
        session_id: str,
        teacher_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve conversation history AND metadata from DynamoDB.

        Args:
            session_id: Unique session identifier
            teacher_id: Teacher's unique identifier

        Returns:
            Dictionary with 'messages' and 'metadata' or None if not found
        """
        try:
            # Query DynamoDB
            response = self.table.get_item(
                Key={
                    "PK": f"CONVERSATION#{teacher_id}",
                    "SK": f"SESSION#{session_id}"
                }
            )

            if "Item" not in response:
                print(f"ℹ️ No conversation history found for session {session_id}")
                return None

            # Deserialize messages
            item = response["Item"]
            messages = [
                self._deserialize_message(msg_dict)
                for msg_dict in item.get("messages", [])
            ]

            metadata = item.get("metadata", {})

            print(f"✅ Retrieved conversation for session {session_id} ({len(messages)} messages, metadata: {metadata})")
            return {
                "messages": messages,
                "metadata": metadata
            }

        except Exception as e:
            print(f"❌ Error retrieving conversation with metadata: {str(e)}")
            return None

    def append_message(
        self,
        session_id: str,
        teacher_id: str,
        message: BaseMessage,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Append a single message to an existing conversation.

        Args:
            session_id: Unique session identifier
            teacher_id: Teacher's unique identifier
            message: Message to append
            metadata: Optional metadata to update

        Returns:
            True if successful, False otherwise
        """
        # Get existing conversation
        existing_messages = self.get_conversation(session_id, teacher_id)

        # If no existing conversation, create new one
        if existing_messages is None:
            existing_messages = []

        # Append new message
        existing_messages.append(message)

        # Save updated conversation
        return self.save_conversation(session_id, teacher_id, existing_messages, metadata)

    def clear_conversation(self, session_id: str, teacher_id: str) -> bool:
        """
        Delete a conversation session from DynamoDB.

        Args:
            session_id: Unique session identifier
            teacher_id: Teacher's unique identifier

        Returns:
            True if successful, False otherwise
        """
        try:
            self.table.delete_item(
                Key={
                    "PK": f"CONVERSATION#{teacher_id}",
                    "SK": f"SESSION#{session_id}"
                }
            )

            print(f"✅ Cleared conversation for session {session_id}")
            return True

        except Exception as e:
            print(f"❌ Error clearing conversation: {str(e)}")
            return False

    def get_all_sessions(self, teacher_id: str, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get all conversation sessions for a teacher.

        Args:
            teacher_id: Teacher's unique identifier
            limit: Maximum number of sessions to return

        Returns:
            List of session summaries
        """
        try:
            response = self.table.query(
                KeyConditionExpression="PK = :pk AND begins_with(SK, :sk)",
                ExpressionAttributeValues={
                    ":pk": f"CONVERSATION#{teacher_id}",
                    ":sk": "SESSION#"
                },
                Limit=limit,
                ScanIndexForward=False  # Most recent first
            )

            sessions = []
            for item in response.get("Items", []):
                sessions.append({
                    "session_id": item.get("session_id"),
                    "message_count": item.get("message_count", 0),
                    "last_updated": item.get("last_updated"),
                    "metadata": item.get("metadata", {})
                })

            print(f"✅ Retrieved {len(sessions)} sessions for teacher {teacher_id}")
            return sessions

        except Exception as e:
            print(f"❌ Error retrieving sessions: {str(e)}")
            return []


# Global instance
conversation_memory = ConversationMemory()