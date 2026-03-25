"""
Unit tests verifying DynamoDB calls go through asyncio.to_thread().

These tests mock asyncio.to_thread and the DynamoDB table to confirm
that every blocking boto3 call is properly wrapped, keeping the
event loop unblocked.
"""

import asyncio
from unittest.mock import MagicMock, patch, AsyncMock

import pytest


# ---------------------------------------------------------------------------
# ChatHistoryService
# ---------------------------------------------------------------------------

class TestChatHistoryServiceAsync:
    """Verify all ChatHistoryService DynamoDB calls use to_thread."""

    @pytest.fixture
    def service(self):
        from app.services.chat_history_service import ChatHistoryService
        mock_table = MagicMock()
        return ChatHistoryService(table=mock_table)

    @pytest.mark.asyncio
    async def test_create_conversation_uses_to_thread(self, service):
        with patch("app.services.chat_history_service.asyncio.to_thread", new_callable=AsyncMock) as mock:
            await service.create_conversation("user1", "thread1")
        mock.assert_called_once()
        assert mock.call_args[0][0] == service.table.put_item

    @pytest.mark.asyncio
    async def test_get_conversation_uses_to_thread(self, service):
        with patch("app.services.chat_history_service.asyncio.to_thread", new_callable=AsyncMock) as mock:
            mock.return_value = {'Item': None}
            await service.get_conversation("user1", "thread1")
        mock.assert_called_once()
        assert mock.call_args[0][0] == service.table.get_item

    @pytest.mark.asyncio
    async def test_get_user_conversations_uses_to_thread(self, service):
        with patch("app.services.chat_history_service.asyncio.to_thread", new_callable=AsyncMock) as mock:
            mock.return_value = {'Items': []}
            await service.get_user_conversations("user1")
        mock.assert_called_once()
        assert mock.call_args[0][0] == service.table.query

    @pytest.mark.asyncio
    async def test_update_title_uses_to_thread(self, service):
        with patch("app.services.chat_history_service.asyncio.to_thread", new_callable=AsyncMock) as mock:
            await service.update_title("user1", "thread1", "Handwriting")
        mock.assert_called_once()
        assert mock.call_args[0][0] == service.table.update_item

    @pytest.mark.asyncio
    async def test_update_preview_uses_to_thread(self, service):
        with patch("app.services.chat_history_service.asyncio.to_thread", new_callable=AsyncMock) as mock:
            await service.update_preview("user1", "thread1", "Hello")
        mock.assert_called_once()
        assert mock.call_args[0][0] == service.table.update_item


# ---------------------------------------------------------------------------
# FeedbackService
# ---------------------------------------------------------------------------

class TestFeedbackServiceAsync:
    """Verify all FeedbackService DynamoDB calls use to_thread."""

    @pytest.fixture
    def service(self):
        from app.services.feedback_service import FeedbackService
        mock_table = MagicMock()
        return FeedbackService(table=mock_table)

    @pytest.mark.asyncio
    async def test_save_feedback_uses_to_thread(self, service):
        with patch("app.services.feedback_service.asyncio.to_thread", new_callable=AsyncMock) as mock:
            await service.save_feedback(
                thread_id="t1", user_id="u1", task_type="handwriting",
                category="lesson", text="Great",
            )
        mock.assert_called_once()
        assert mock.call_args[0][0] == service.table.put_item

    @pytest.mark.asyncio
    async def test_get_feedback_by_thread_uses_to_thread(self, service):
        with patch("app.services.feedback_service.asyncio.to_thread", new_callable=AsyncMock) as mock:
            mock.return_value = {'Items': []}
            await service.get_feedback_by_thread("t1")
        mock.assert_called_once()
        assert mock.call_args[0][0] == service.table.query

    @pytest.mark.asyncio
    async def test_get_feedback_by_user_uses_to_thread(self, service):
        with patch("app.services.feedback_service.asyncio.to_thread", new_callable=AsyncMock) as mock:
            mock.return_value = {'Items': []}
            await service.get_feedback_by_user("u1")
        mock.assert_called_once()
        assert mock.call_args[0][0] == service.table.query


# ---------------------------------------------------------------------------
# AuthService
# ---------------------------------------------------------------------------

class TestAuthServiceAsync:
    """Verify all AuthService DynamoDB calls use to_thread."""

    @pytest.fixture
    def service(self):
        from app.services.auth_service import AuthService
        svc = AuthService.__new__(AuthService)
        svc.table = MagicMock()
        return svc

    @pytest.mark.asyncio
    async def test_get_user_by_email_uses_to_thread(self, service):
        with patch("app.services.auth_service.asyncio.to_thread", new_callable=AsyncMock) as mock:
            mock.return_value = {'Items': []}
            await service.get_user_by_email("a@b.com")
        mock.assert_called_once()
        assert mock.call_args[0][0] == service.table.query

    @pytest.mark.asyncio
    async def test_get_user_by_id_uses_to_thread(self, service):
        with patch("app.services.auth_service.asyncio.to_thread", new_callable=AsyncMock) as mock:
            mock.return_value = {}
            await service.get_user_by_id("uid")
        mock.assert_called_once()
        assert mock.call_args[0][0] == service.table.get_item

    @pytest.mark.asyncio
    async def test_create_user_uses_to_thread(self, service):
        from app.schemas.auth import UserCreate
        with patch("app.services.auth_service.asyncio.to_thread", new_callable=AsyncMock) as mock:
            # First call = get_user_by_email (query), second = put_item
            mock.side_effect = [{'Items': []}, None]
            await service.create_user(UserCreate(
                email="new@test.com", password="pass1234", full_name="Test"
            ))
        assert mock.call_count == 2
        assert mock.call_args_list[0][0][0] == service.table.query
        assert mock.call_args_list[1][0][0] == service.table.put_item

    @pytest.mark.asyncio
    async def test_authenticate_user_uses_to_thread(self, service):
        with patch("app.services.auth_service.asyncio.to_thread", new_callable=AsyncMock) as mock:
            mock.return_value = {'Items': []}
            result = await service.authenticate_user("a@b.com", "pass")
        # get_user_by_email returns None → early return, only 1 call
        mock.assert_called_once()
        assert mock.call_args[0][0] == service.table.query
        assert result is None

    @pytest.mark.asyncio
    async def test_store_refresh_token_uses_to_thread(self, service):
        with patch("app.services.auth_service.asyncio.to_thread", new_callable=AsyncMock) as mock:
            await service.store_refresh_token("uid", "tid")
        mock.assert_called_once()
        assert mock.call_args[0][0] == service.table.put_item

    @pytest.mark.asyncio
    async def test_is_refresh_token_valid_uses_to_thread(self, service):
        with patch("app.services.auth_service.asyncio.to_thread", new_callable=AsyncMock) as mock:
            mock.return_value = {}
            await service.is_refresh_token_valid("uid", "tid")
        mock.assert_called_once()
        assert mock.call_args[0][0] == service.table.get_item

    @pytest.mark.asyncio
    async def test_revoke_refresh_token_uses_to_thread(self, service):
        with patch("app.services.auth_service.asyncio.to_thread", new_callable=AsyncMock) as mock:
            await service.revoke_refresh_token("uid", "tid")
        mock.assert_called_once()
        assert mock.call_args[0][0] == service.table.delete_item

    @pytest.mark.asyncio
    async def test_revoke_all_refresh_tokens_uses_to_thread(self, service):
        with patch("app.services.auth_service.asyncio.to_thread", new_callable=AsyncMock) as mock:
            # First call = query, second = delete_item
            mock.side_effect = [
                {'Items': [{'PK': 'USER#uid', 'SK': 'REFRESH_TOKEN#t1'}]},
                None,
            ]
            count = await service.revoke_all_refresh_tokens("uid")
        assert mock.call_count == 2
        assert mock.call_args_list[0][0][0] == service.table.query
        assert mock.call_args_list[1][0][0] == service.table.delete_item
        assert count == 1
