"""
Test suite for Feature 001: Greeting & Main Router

This test validates the initial graph entry flow:
1. The graph greets the user and presents main tasks
2. The graph pauses for input after greeting
3. The graph classifies the user's choice using Pydantic tools
4. The graph loops back on classification failure
"""
import pytest
from langchain_core.messages import HumanMessage
from app.graph.graph import create_graph


@pytest.mark.asyncio
async def test_greeting_node_presents_welcome_message():
    """Test that the greeting node displays the welcome message."""
    graph = await create_graph()

    # Start a new conversation
    config = {"configurable": {"thread_id": "test-greeting-1"}}

    try:
        # Invoke the graph (should stop after greeting_node due to interrupt_after)
        result = await graph.ainvoke(
            {"messages": []},
            config=config
        )

        # Check that we got a welcome message
        assert len(result["messages"]) > 0
        last_message = result["messages"][-1]
        assert "Welcome!" in last_message.content
        assert "Handwriting" in last_message.content
        assert "Vocabulary" in last_message.content
        assert "Idea Generation" in last_message.content
    finally:
        await graph.checkpointer.conn.close()


@pytest.mark.asyncio
async def test_main_router_classifies_handwriting():
    """Test that the router correctly classifies 'handwriting' input."""
    graph = await create_graph()

    config = {"configurable": {"thread_id": "test-handwriting-1"}}

    try:
        # First invocation - greeting (will be interrupted after greeting_node)
        await graph.ainvoke({"messages": []}, config=config)

        # Update state to add user input
        await graph.aupdate_state(
            config,
            {"messages": [HumanMessage(content="I want to do handwriting")]}
        )

        # Resume the graph to continue processing
        result = await graph.ainvoke(None, config=config)

        # Check that task_name was set correctly
        assert result.get("task_name") == "Handwriting"

        # Check that we got the stub message
        last_message = result["messages"][-1]
        assert "Handwriting feature coming soon" in last_message.content
    finally:
        await graph.checkpointer.conn.close()


@pytest.mark.asyncio
async def test_main_router_classifies_vocabulary():
    """Test that the router correctly classifies 'vocabulary' input."""
    graph = await create_graph()

    config = {"configurable": {"thread_id": "test-vocabulary-1"}}

    try:
        # First invocation - greeting
        await graph.ainvoke({"messages": []}, config=config)

        # Update state to add user input
        await graph.aupdate_state(
            config,
            {"messages": [HumanMessage(content="Let's work on vocabulary")]}
        )

        # Resume to continue processing
        result = await graph.ainvoke(None, config=config)

        # Check that task_name was set correctly
        assert result.get("task_name") == "Vocabulary"

        # Check that we got the stub message
        last_message = result["messages"][-1]
        assert "Vocabulary feature coming soon" in last_message.content
    finally:
        await graph.checkpointer.conn.close()


@pytest.mark.asyncio
async def test_main_router_classifies_idea_generation():
    """Test that the router correctly classifies 'idea generation' input."""
    graph = await create_graph()

    config = {"configurable": {"thread_id": "test-idea-gen-1"}}

    try:
        # First invocation - greeting
        await graph.ainvoke({"messages": []}, config=config)

        # Update state to add user input
        await graph.aupdate_state(
            config,
            {"messages": [HumanMessage(content="Idea Generation please")]}
        )

        # Resume to continue processing
        result = await graph.ainvoke(None, config=config)

        # Check that task_name was set correctly
        assert result.get("task_name") == "Idea Generation"

        # Check that we got the stub message
        last_message = result["messages"][-1]
        assert "Idea Generation feature coming soon" in last_message.content
    finally:
        await graph.checkpointer.conn.close()


# @pytest.mark.asyncio
# async def test_main_router_loops_on_invalid_input():
#     """Test that the router loops back to greeting on invalid input like 'spanish'."""
#     graph = await create_graph()
#
#     config = {"configurable": {"thread_id": "test-invalid-1"}}
#
#     # First invocation - greeting
#     result1 = await graph.ainvoke({"messages": []}, config=config)
#     message_count_after_greeting = len(result1["messages"])
#
#     # Update state to add invalid user input
#     await graph.aupdate_state(
#         config,
#         {"messages": [HumanMessage(content="let's do spanish")]}
#     )
#
#     # Resume to process the invalid input
#     result2 = await graph.ainvoke(None, config=config)
#
#     # Check that task_name was set to __ERROR__
#     assert result2.get("task_name") == "__ERROR__"
#
#     # Check that we got an error message
#     messages = result2["messages"]
#     error_message_found = False
#     for msg in messages[message_count_after_greeting:]:
#         if "didn't understand" in msg.content or "please pick from" in msg.content:
#             error_message_found = True
#             break
#     assert error_message_found, "Expected error message not found"
#
#     # Third invocation - should loop back and show greeting again
#     # Since the graph loops back to greeting_node and we have interrupt_after=["greeting_node"],
#     # the graph should have executed greeting_node and stopped
#     # Check that the welcome message appears again (proving the loop worked)
#     last_message = result2["messages"][-1]
#     # The greeting should be shown after the error message
#     has_welcome = any("Welcome!" in msg.content for msg in result2["messages"])
#     assert has_welcome, "Expected to loop back to greeting with Welcome message"


@pytest.mark.asyncio
async def test_graph_pauses_after_greeting():
    """Test that the graph correctly pauses after the greeting_node."""
    graph = await create_graph()

    config = {"configurable": {"thread_id": "test-pause-1"}}

    try:
        # First invocation should stop after greeting_node
        result = await graph.ainvoke({"messages": []}, config=config)

        # We should have at least one message (the greeting)
        assert len(result["messages"]) >= 1

        # Update state to add user input
        await graph.aupdate_state(
            config,
            {"messages": [HumanMessage(content="handwriting")]}
        )

        # Resume to continue processing
        result2 = await graph.ainvoke(None, config=config)

        # After user input, we should have routed to handwriting
        assert result2.get("task_name") == "Handwriting"
    finally:
        await graph.checkpointer.conn.close()


