"""
Unit tests for DynamoDB checkpointer integration.
Tests that graph state persists correctly using DynamoDB Local.
"""

import pytest
from langchain_core.messages import HumanMessage

from app.graph.graph import create_graph
from app.config import settings


class TestCheckpointerPersistence:
    """Tests for checkpointer state persistence."""

    @pytest.mark.asyncio
    async def test_checkpointer_saves_state(self):
        """Test that checkpointer saves graph state to DynamoDB."""
        graph = await create_graph()
        thread_id = "test-persist-001"
        config = {"configurable": {"thread_id": thread_id}}

        # Invoke graph with a message
        await graph.ainvoke({"messages": [HumanMessage(content="Hello")]}, config=config)

        # Verify state was saved by retrieving it
        state = await graph.aget_state(config)
        assert state is not None
        assert len(state.values.get("messages", [])) > 0

    @pytest.mark.asyncio
    async def test_checkpointer_retrieves_state(self):
        """Test that checkpointer can retrieve previously saved state."""
        graph = await create_graph()
        thread_id = "test-retrieve-001"
        config = {"configurable": {"thread_id": thread_id}}

        # First invocation
        await graph.ainvoke({"messages": [HumanMessage(content="I want handwriting")]}, config=config)

        # Create a new graph instance (simulating server restart)
        graph2 = await create_graph()

        # Should be able to retrieve state from the same thread_id
        state = await graph2.aget_state(config)
        assert state is not None
        messages = state.values.get("messages", [])
        assert len(messages) > 0


class TestConversationResume:
    """Tests for resuming conversations from checkpoints."""

    @pytest.mark.asyncio
    async def test_conversation_resume_with_thread_id(self):
        """Test that conversation can be resumed using thread_id."""
        graph = await create_graph()
        thread_id = "test-resume-001"
        config = {"configurable": {"thread_id": thread_id}}

        # First message - should trigger greeting then interrupt
        await graph.ainvoke({"messages": []}, config=config)

        # Get initial state
        state1 = await graph.aget_state(config)
        initial_message_count = len(state1.values.get("messages", []))

        # Resume with user message
        await graph.aupdate_state(
            config,
            {"messages": [HumanMessage(content="I want to practice handwriting")]}
        )
        await graph.ainvoke(None, config=config)

        # Verify state accumulated
        state2 = await graph.aget_state(config)
        final_message_count = len(state2.values.get("messages", []))
        assert final_message_count > initial_message_count

    @pytest.mark.asyncio
    async def test_task_name_persists_after_routing(self):
        """Test that task_name is set and persisted after main_router."""
        graph = await create_graph()
        thread_id = "test-taskname-001"
        config = {"configurable": {"thread_id": thread_id}}

        # Start conversation
        await graph.ainvoke({"messages": []}, config=config)

        # Send message that should route to handwriting
        await graph.aupdate_state(
            config,
            {"messages": [HumanMessage(content="handwriting")]}
        )
        await graph.ainvoke(None, config=config)

        # Check task_name was set
        state = await graph.aget_state(config)
        task_name = state.values.get("task_name")
        assert task_name is not None
        assert task_name in ["Handwriting", "handwriting", "__CLARIFY__"]


class TestMultipleThreads:
    """Tests for handling multiple conversation threads."""

    @pytest.mark.asyncio
    async def test_separate_threads_have_separate_state(self):
        """Test that different thread_ids maintain separate state."""
        graph = await create_graph()

        thread1_config = {"configurable": {"thread_id": "test-thread-a"}}
        thread2_config = {"configurable": {"thread_id": "test-thread-b"}}

        # Invoke on thread 1
        await graph.ainvoke({"messages": [HumanMessage(content="Thread 1 message")]}, config=thread1_config)

        # Invoke on thread 2
        await graph.ainvoke({"messages": [HumanMessage(content="Thread 2 message")]}, config=thread2_config)

        # Verify states are separate
        state1 = await graph.aget_state(thread1_config)
        state2 = await graph.aget_state(thread2_config)

        # Each should have their own messages
        messages1 = [m.content for m in state1.values.get("messages", []) if hasattr(m, 'content')]
        messages2 = [m.content for m in state2.values.get("messages", []) if hasattr(m, 'content')]

        # At least one message in each should contain their unique content
        assert any("Thread 1" in m for m in messages1)
        assert any("Thread 2" in m for m in messages2)


class TestCheckpointerErrorHandling:
    """Tests for error handling scenarios."""

    @pytest.mark.asyncio
    async def test_nonexistent_thread_returns_empty_state(self):
        """Test that querying non-existent thread doesn't crash."""
        graph = await create_graph()
        config = {"configurable": {"thread_id": "nonexistent-thread-xyz"}}

        # Should not raise, just return None or empty state
        state = await graph.aget_state(config)
        # State might be None or have empty/default values
        if state is not None:
            messages = state.values.get("messages", [])
            assert messages == [] or messages is None
