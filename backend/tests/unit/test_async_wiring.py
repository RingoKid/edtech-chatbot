"""
Unit tests verifying async wiring across the app:

1. DynamoDB calls go through asyncio.to_thread()
2. Graph nodes that do I/O are async and use .ainvoke() (not .invoke())
"""

import ast
import asyncio
import inspect
import textwrap
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
        from app.core.security import get_password_hash
        with patch("app.services.auth_service.asyncio.to_thread", new_callable=AsyncMock) as mock:
            # call 1 = get_user_by_email (query), 2 = get_password_hash, 3 = put_item
            mock.side_effect = [{'Items': []}, 'hashed_pw', None]
            await service.create_user(UserCreate(
                email="new@test.com", password="pass1234", full_name="Test"
            ))
        assert mock.call_count == 3
        assert mock.call_args_list[0][0][0] == service.table.query
        assert mock.call_args_list[1][0][0] == get_password_hash
        assert mock.call_args_list[2][0][0] == service.table.put_item

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
    async def test_authenticate_user_bcrypt_uses_to_thread(self, service):
        from app.core.security import verify_password
        fake_user = {
            'PK': 'USER#u1', 'SK': 'PROFILE', 'GSI1PK': 'EMAIL#a@b.com',
            'GSI1SK': 'USER#u1', 'user_id': 'u1', 'email': 'a@b.com',
            'hashed_password': 'fakehash', 'full_name': 'Test',
            'role': 'USER', 'created_at': '2026-01-01', 'updated_at': '2026-01-01',
        }
        with patch("app.services.auth_service.asyncio.to_thread", new_callable=AsyncMock) as mock:
            # call 1 = query (finds user), call 2 = verify_password (returns False)
            mock.side_effect = [{'Items': [fake_user]}, False]
            result = await service.authenticate_user("a@b.com", "wrong")
        assert mock.call_count == 2
        assert mock.call_args_list[0][0][0] == service.table.query
        assert mock.call_args_list[1][0][0] == verify_password
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


# ---------------------------------------------------------------------------
# Database init (lifespan-based, not import-time)
# ---------------------------------------------------------------------------

class TestDatabaseInit:
    """Verify database uses lifespan init, not module-level init."""

    def setup_method(self):
        """Reset module globals before each test."""
        import app.database as db
        db._dynamodb = None
        db._table = None

    def teardown_method(self):
        """Re-init so other tests aren't affected."""
        import app.database as db
        db.init_db()

    def test_get_db_raises_before_init(self):
        """get_db() must raise if init_db() hasn't been called."""
        from app.database import get_db
        with pytest.raises(RuntimeError, match="not initialized"):
            get_db()

    def test_get_dynamodb_raises_before_init(self):
        """get_dynamodb() must raise if init_db() hasn't been called."""
        from app.database import get_dynamodb
        with pytest.raises(RuntimeError, match="not initialized"):
            get_dynamodb()

    def test_init_db_sets_globals(self):
        """init_db() should populate both _dynamodb and _table."""
        import app.database as db
        db.init_db()
        assert db._dynamodb is not None
        assert db._table is not None

    def test_get_db_returns_table_after_init(self):
        """get_db() returns the table after init_db()."""
        import app.database as db
        db.init_db()
        table = db.get_db()
        assert table is db._table

    @pytest.mark.asyncio
    async def test_lifespan_calls_init_db(self):
        """FastAPI lifespan handler must call init_db()."""
        import app.main as main_module
        import app.database as db

        assert db._table is None  # reset by setup_method
        async with main_module.lifespan(main_module.app):
            pass
        assert db._table is not None


# ---------------------------------------------------------------------------
# Graph node async checks (auto-discovered from graph definition)
# ---------------------------------------------------------------------------

class TestGraphNodesAsync:
    """Verify graph nodes that do I/O are async and don't use blocking calls.

    Nodes are auto-discovered from graph.add_node() calls in create_graph().
    Pure-function nodes (no I/O) are exempt via SYNC_ALLOWLIST.
    """

    # Pure-function nodes with no I/O — intentionally sync
    SYNC_ALLOWLIST = {
        "image_assembly_node",
        "handwriting_placeholder",
        "vocabulary_placeholder",
        "idea_generation_placeholder",
        "vocabulary_generator_placeholder",
        "idea_generation_generator_placeholder",
    }

    @staticmethod
    def _get_graph_node_functions() -> dict:
        """Auto-discover all node functions registered in create_graph()."""
        import sys
        from app.graph.graph import create_graph  # noqa: F401 — forces module load
        graph_module = sys.modules['app.graph.graph']

        source = inspect.getsource(create_graph)
        tree = ast.parse(textwrap.dedent(source))

        nodes = {}
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "add_node"
                and len(node.args) >= 2
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[1], ast.Name)
            ):
                name = node.args[0].value
                func_name = node.args[1].id
                func = getattr(graph_module, func_name, None)
                if func is not None:
                    nodes[name] = func

        return nodes

    def test_discovers_nodes(self):
        """Sanity check: auto-discovery finds the nodes we expect."""
        nodes = self._get_graph_node_functions()
        assert len(nodes) >= 4, f"Expected at least 4 nodes, found {len(nodes)}: {list(nodes)}"

    def test_io_nodes_are_async(self):
        """Every node not on the sync allowlist must be async def."""
        nodes = self._get_graph_node_functions()

        non_async = [
            name for name, func in nodes.items()
            if func.__name__ not in self.SYNC_ALLOWLIST
            and not inspect.iscoroutinefunction(func)
        ]

        assert not non_async, (
            f"Graph nodes must be async def (or added to SYNC_ALLOWLIST if pure): {non_async}"
        )

    def test_no_sync_invoke_in_nodes(self):
        """No graph node should call .invoke() — must use .ainvoke() instead."""
        nodes = self._get_graph_node_functions()

        violations = []
        for name, func in nodes.items():
            source = textwrap.dedent(inspect.getsource(func))
            tree = ast.parse(source)

            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "invoke"
                ):
                    violations.append(name)
                    break

        assert not violations, (
            f"Graph nodes must use .ainvoke(), not .invoke(): {violations}"
        )

    def test_no_time_sleep_in_nodes(self):
        """No graph node should call time.sleep() — blocks the event loop."""
        nodes = self._get_graph_node_functions()

        violations = []
        for name, func in nodes.items():
            source = textwrap.dedent(inspect.getsource(func))
            tree = ast.parse(source)

            for node in ast.walk(tree):
                if (
                    isinstance(node, ast.Call)
                    and isinstance(node.func, ast.Attribute)
                    and node.func.attr == "sleep"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id == "time"
                ):
                    violations.append(name)
                    break

        assert not violations, (
            f"Graph nodes must not use time.sleep() (blocks event loop): {violations}"
        )
