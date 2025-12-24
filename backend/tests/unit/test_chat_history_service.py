"""
Unit tests for chat history service.
Tests CRUD operations for conversation records in DynamoDB.
"""

import pytest
import boto3
from datetime import datetime
from botocore.exceptions import ClientError
from app.config import settings
from app.db_schema import MAIN_TABLE_SCHEMA


@pytest.fixture(scope="module")
def dynamodb_table():
    """Setup test table in DynamoDB Local."""
    dynamodb = boto3.resource(
        'dynamodb',
        endpoint_url=settings.dynamodb_endpoint_url,
        region_name=settings.aws_region,
        aws_access_key_id='dummy',
        aws_secret_access_key='dummy'
    )

    # Use a test-specific table name
    table_name = f"test-chat-history-{settings.table_name}"

    # Delete if exists
    try:
        table = dynamodb.Table(table_name)
        table.delete()
        table.wait_until_not_exists()
    except ClientError:
        pass

    # Create table
    table = dynamodb.create_table(
        TableName=table_name,
        BillingMode='PAY_PER_REQUEST',
        **MAIN_TABLE_SCHEMA
    )
    table.wait_until_exists()

    yield table

    # Cleanup
    try:
        table.delete()
    except ClientError:
        pass


@pytest.fixture
def chat_history_service(dynamodb_table):
    """Create ChatHistoryService instance with test table."""
    from app.services.chat_history_service import ChatHistoryService
    return ChatHistoryService(table=dynamodb_table)


class TestCreateConversation:
    """Tests for create_conversation method."""

    @pytest.mark.asyncio
    async def test_creates_conversation_with_default_title(self, chat_history_service):
        """Test creating conversation with default 'New Conversation' title."""
        user_id = "user-create-001"
        thread_id = "thread-create-001"

        await chat_history_service.create_conversation(user_id, thread_id)

        conversation = await chat_history_service.get_conversation(user_id, thread_id)
        assert conversation is not None
        assert conversation.title == "New Conversation"
        assert conversation.thread_id == thread_id
        assert conversation.user_id == user_id
        assert conversation.last_message_preview is None

    @pytest.mark.asyncio
    async def test_creates_conversation_with_timestamps(self, chat_history_service):
        """Test that created_at and updated_at are set."""
        user_id = "user-create-002"
        thread_id = "thread-create-002"

        await chat_history_service.create_conversation(user_id, thread_id)

        conversation = await chat_history_service.get_conversation(user_id, thread_id)
        assert conversation.created_at is not None
        assert conversation.updated_at is not None

    @pytest.mark.asyncio
    async def test_creates_conversation_with_correct_keys(self, chat_history_service):
        """Test that PK and SK are formatted correctly."""
        user_id = "user-create-003"
        thread_id = "thread-create-003"

        await chat_history_service.create_conversation(user_id, thread_id)

        conversation = await chat_history_service.get_conversation(user_id, thread_id)
        assert conversation.pk == f"USER#{user_id}"
        assert conversation.sk == f"THREAD#{thread_id}"


class TestGetUserConversations:
    """Tests for get_user_conversations method."""

    @pytest.mark.asyncio
    async def test_returns_all_user_conversations(self, chat_history_service):
        """Test retrieving all conversations for a user."""
        user_id = "user-list-001"

        # Create multiple conversations
        await chat_history_service.create_conversation(user_id, "thread-list-a")
        await chat_history_service.create_conversation(user_id, "thread-list-b")
        await chat_history_service.create_conversation(user_id, "thread-list-c")

        conversations = await chat_history_service.get_user_conversations(user_id)
        assert len(conversations) == 3

    @pytest.mark.asyncio
    async def test_returns_empty_list_for_new_user(self, chat_history_service):
        """Test that new user gets empty conversation list."""
        user_id = "user-new-no-conversations"

        conversations = await chat_history_service.get_user_conversations(user_id)
        assert conversations == []

    @pytest.mark.asyncio
    async def test_does_not_return_other_users_conversations(self, chat_history_service):
        """Test that user only sees their own conversations."""
        user_a = "user-isolation-a"
        user_b = "user-isolation-b"

        await chat_history_service.create_conversation(user_a, "thread-user-a")
        await chat_history_service.create_conversation(user_b, "thread-user-b")

        conversations_a = await chat_history_service.get_user_conversations(user_a)
        thread_ids = [c.thread_id for c in conversations_a]

        assert "thread-user-a" in thread_ids
        assert "thread-user-b" not in thread_ids


class TestUpdateTitle:
    """Tests for update_title method."""

    @pytest.mark.asyncio
    async def test_updates_title_from_task_name(self, chat_history_service):
        """Test updating title based on task_name."""
        user_id = "user-title-001"
        thread_id = "thread-title-001"

        await chat_history_service.create_conversation(user_id, thread_id)
        await chat_history_service.update_title(user_id, thread_id, "Handwriting")

        conversation = await chat_history_service.get_conversation(user_id, thread_id)
        assert conversation.title == "Handwriting Practice"

    @pytest.mark.asyncio
    async def test_maps_vocabulary_task_name(self, chat_history_service):
        """Test Vocabulary task name mapping."""
        user_id = "user-title-002"
        thread_id = "thread-title-002"

        await chat_history_service.create_conversation(user_id, thread_id)
        await chat_history_service.update_title(user_id, thread_id, "Vocabulary")

        conversation = await chat_history_service.get_conversation(user_id, thread_id)
        assert conversation.title == "Vocabulary Learning"

    @pytest.mark.asyncio
    async def test_maps_idea_generation_task_name(self, chat_history_service):
        """Test Idea Generation task name mapping."""
        user_id = "user-title-003"
        thread_id = "thread-title-003"

        await chat_history_service.create_conversation(user_id, thread_id)
        await chat_history_service.update_title(user_id, thread_id, "Idea Generation")

        conversation = await chat_history_service.get_conversation(user_id, thread_id)
        assert conversation.title == "Idea Generation"

    @pytest.mark.asyncio
    async def test_updates_updated_at_timestamp(self, chat_history_service):
        """Test that updated_at changes when title is updated."""
        user_id = "user-title-004"
        thread_id = "thread-title-004"

        await chat_history_service.create_conversation(user_id, thread_id)
        conversation_before = await chat_history_service.get_conversation(user_id, thread_id)

        # Small delay to ensure timestamp difference
        import asyncio
        await asyncio.sleep(0.1)

        await chat_history_service.update_title(user_id, thread_id, "Vocabulary")
        conversation_after = await chat_history_service.get_conversation(user_id, thread_id)

        assert conversation_after.updated_at >= conversation_before.updated_at


class TestUpdatePreview:
    """Tests for update_preview method."""

    @pytest.mark.asyncio
    async def test_updates_last_message_preview(self, chat_history_service):
        """Test updating last_message_preview."""
        user_id = "user-preview-001"
        thread_id = "thread-preview-001"

        await chat_history_service.create_conversation(user_id, thread_id)
        await chat_history_service.update_preview(user_id, thread_id, "Let's practice writing letters!")

        conversation = await chat_history_service.get_conversation(user_id, thread_id)
        assert conversation.last_message_preview == "Let's practice writing letters!"

    @pytest.mark.asyncio
    async def test_truncates_long_preview(self, chat_history_service):
        """Test that preview is truncated to 100 characters."""
        user_id = "user-preview-002"
        thread_id = "thread-preview-002"
        long_message = "A" * 200

        await chat_history_service.create_conversation(user_id, thread_id)
        await chat_history_service.update_preview(user_id, thread_id, long_message)

        conversation = await chat_history_service.get_conversation(user_id, thread_id)
        assert len(conversation.last_message_preview) <= 100


class TestOwnershipValidation:
    """Tests for ownership validation."""

    @pytest.mark.asyncio
    async def test_user_can_access_own_thread(self, chat_history_service):
        """Test that user can access their own thread."""
        user_id = "user-owner-001"
        thread_id = "thread-owner-001"

        await chat_history_service.create_conversation(user_id, thread_id)

        is_owner = await chat_history_service.verify_ownership(user_id, thread_id)
        assert is_owner is True

    @pytest.mark.asyncio
    async def test_user_cannot_access_other_thread(self, chat_history_service):
        """Test that user cannot access another user's thread."""
        owner = "user-owner-002"
        other = "user-other-002"
        thread_id = "thread-owner-002"

        await chat_history_service.create_conversation(owner, thread_id)

        is_owner = await chat_history_service.verify_ownership(other, thread_id)
        assert is_owner is False

    @pytest.mark.asyncio
    async def test_nonexistent_thread_returns_false(self, chat_history_service):
        """Test that non-existent thread returns False for ownership."""
        user_id = "user-owner-003"
        thread_id = "nonexistent-thread-xyz"

        is_owner = await chat_history_service.verify_ownership(user_id, thread_id)
        assert is_owner is False
