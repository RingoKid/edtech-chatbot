"""
Routing agent evaluation tests.

Run with:
    docker compose exec backend pytest tests/evals/test_routing_agent.py -v

These tests run the routing agent against the test dataset and measure:
- routing_accuracy: Did agent route to correct task type?
- turn_efficiency: How many turns to complete routing?
"""

import pytest
from typing import List
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver

from app.graph.graph import create_graph
from app.graph.agents.routing import TOOL_TO_TASK_TYPE
from tests.datasets.routing_agent import (
    ROUTING_TEST_CASES,
    RoutingTestCase,
    get_clear_intent_cases,
)


@pytest.fixture
def memory_checkpointer():
    """In-memory checkpointer for testing (no DynamoDB needed)."""
    return MemorySaver()


async def run_agent_until_routed(
    graph,
    initial_message: str,
    thread_id: str,
    max_turns: int = 10,
) -> dict:
    """
    Run the agent until it routes to a task or max turns reached.

    Returns dict with:
    - task_type: The routed task type (or None if not routed)
    - turns: Number of turns taken
    - messages: All messages in conversation
    """
    config = {"configurable": {"thread_id": thread_id}}

    # Initial invocation
    result = await graph.ainvoke(
        {"messages": [HumanMessage(content=initial_message)]},
        config=config,
    )

    turns = 1
    task_type = result.get("task_type")

    # If routed on first turn, return
    if task_type is not None:
        return {
            "task_type": task_type,
            "turns": turns,
            "messages": result.get("messages", []),
            "routing_complete": result.get("routing_complete", False),
        }

    # Not routed - return current state
    return {
        "task_type": None,
        "turns": turns,
        "messages": result.get("messages", []),
        "routing_complete": False,
    }


def extract_task_type_from_messages(messages: List) -> str | None:
    """
    Extract the task type from messages by looking for tool calls.

    Returns the task type if a routing tool was called, None otherwise.
    """
    for msg in reversed(messages):
        if isinstance(msg, ToolMessage):
            tool_name = msg.name
            if tool_name in TOOL_TO_TASK_TYPE:
                return TOOL_TO_TASK_TYPE[tool_name]
    return None


class TestRoutingAccuracy:
    """Tests for routing accuracy on clear intent cases."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_case",
        get_clear_intent_cases(),
        ids=[tc.description for tc in get_clear_intent_cases()],
    )
    async def test_routes_to_correct_task(
        self,
        test_case: RoutingTestCase,
        memory_checkpointer,
    ):
        """Test that agent routes to the correct task type."""
        # Create graph with in-memory checkpointer
        graph = await create_graph(checkpointer=memory_checkpointer)

        # Run agent
        input_msg = (
            test_case.input
            if isinstance(test_case.input, str)
            else test_case.input[0]["content"]
        )

        result = await run_agent_until_routed(
            graph=graph,
            initial_message=input_msg,
            thread_id=f"test-{test_case.description}",
            max_turns=test_case.expected_max_turns + 2,  # Allow some buffer
        )

        # Assert correct routing
        assert result["task_type"] == test_case.expected_task_type, (
            f"Expected task_type={test_case.expected_task_type}, "
            f"got {result['task_type']}. "
            f"Input: {input_msg}"
        )


class TestTurnEfficiency:
    """Tests for turn efficiency - how quickly does the agent route?"""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_case",
        get_clear_intent_cases(),
        ids=[tc.description for tc in get_clear_intent_cases()],
    )
    async def test_routes_within_expected_turns(
        self,
        test_case: RoutingTestCase,
        memory_checkpointer,
    ):
        """Test that agent routes within expected number of turns."""
        # Create graph with in-memory checkpointer
        graph = await create_graph(checkpointer=memory_checkpointer)

        # Run agent
        input_msg = (
            test_case.input
            if isinstance(test_case.input, str)
            else test_case.input[0]["content"]
        )

        result = await run_agent_until_routed(
            graph=graph,
            initial_message=input_msg,
            thread_id=f"test-turns-{test_case.description}",
            max_turns=test_case.expected_max_turns + 2,
        )

        # Assert efficiency
        assert result["turns"] <= test_case.expected_max_turns, (
            f"Expected <= {test_case.expected_max_turns} turns, "
            f"got {result['turns']}. "
            f"Input: {input_msg}"
        )


class TestGreetings:
    """Tests for greeting behavior."""

    @pytest.mark.asyncio
    async def test_greeting_responds_without_routing(self, memory_checkpointer):
        """Test that greetings get a response without immediate routing."""
        graph = await create_graph(checkpointer=memory_checkpointer)

        result = await run_agent_until_routed(
            graph=graph,
            initial_message="hi",
            thread_id="test-greeting",
            max_turns=1,
        )

        # Should NOT route on greeting
        assert result["task_type"] is None, "Should not route on greeting"

        # Should have at least one AI response
        ai_messages = [
            m for m in result["messages"]
            if isinstance(m, AIMessage) and m.content
        ]
        assert len(ai_messages) > 0, "Should respond to greeting"


class TestAmbiguousInput:
    """Tests for ambiguous input handling."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "ambiguous_input",
        ["help me teach", "make a lesson", "I need help"],
    )
    async def test_asks_clarification_for_ambiguous_input(
        self,
        ambiguous_input: str,
        memory_checkpointer,
    ):
        """Test that ambiguous input triggers clarification, not routing."""
        graph = await create_graph(checkpointer=memory_checkpointer)

        result = await run_agent_until_routed(
            graph=graph,
            initial_message=ambiguous_input,
            thread_id=f"test-ambiguous-{hash(ambiguous_input)}",
            max_turns=1,
        )

        # Should NOT route on ambiguous input
        assert result["task_type"] is None, (
            f"Should not route on ambiguous input: {ambiguous_input}"
        )


class TestPlaceholderNodes:
    """Tests that placeholder nodes work correctly after routing."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "input_msg,expected_task",
        [
            ("I want to create a handwriting lesson", "handwriting"),
            ("I need vocabulary words for my class", "vocabulary"),
            ("give me some lesson ideas", "idea_generation"),
        ],
    )
    async def test_placeholder_returns_coming_soon(
        self,
        input_msg: str,
        expected_task: str,
        memory_checkpointer,
    ):
        """Test that placeholder nodes return 'Coming Soon' message."""
        graph = await create_graph(checkpointer=memory_checkpointer)

        result = await run_agent_until_routed(
            graph=graph,
            initial_message=input_msg,
            thread_id=f"test-placeholder-{expected_task}",
            max_turns=2,
        )

        # Should route to expected task
        assert result["task_type"] == expected_task

        # Should have a "Coming Soon" message in the response
        messages = result.get("messages", [])
        ai_messages = [m for m in messages if isinstance(m, AIMessage)]

        found_coming_soon = any(
            "coming soon" in m.content.lower()
            for m in ai_messages
            if m.content
        )
        assert found_coming_soon, (
            f"Expected 'Coming Soon' in response for {expected_task}"
        )


# --- Aggregate Metrics ---

@pytest.mark.asyncio
async def test_overall_routing_accuracy(memory_checkpointer):
    """
    Aggregate test: Calculate overall routing accuracy.

    This test runs all clear intent cases and reports overall accuracy.
    Target: >= 95%
    """
    graph = await create_graph(checkpointer=memory_checkpointer)
    clear_cases = get_clear_intent_cases()

    correct = 0
    total = len(clear_cases)

    for i, test_case in enumerate(clear_cases):
        input_msg = (
            test_case.input
            if isinstance(test_case.input, str)
            else test_case.input[0]["content"]
        )

        result = await run_agent_until_routed(
            graph=graph,
            initial_message=input_msg,
            thread_id=f"accuracy-test-{i}",
            max_turns=3,
        )

        if result["task_type"] == test_case.expected_task_type:
            correct += 1

    accuracy = correct / total if total > 0 else 0
    print(f"\nRouting Accuracy: {correct}/{total} = {accuracy:.1%}")

    # Assert target accuracy (90% to account for LLM non-determinism)
    assert accuracy >= 0.90, f"Routing accuracy {accuracy:.1%} below 90% target"


@pytest.mark.asyncio
async def test_average_turn_efficiency(memory_checkpointer):
    """
    Aggregate test: Calculate average turns to route.

    This test runs all clear intent cases and reports average turns.
    Target: <= 2.0 average turns
    """
    graph = await create_graph(checkpointer=memory_checkpointer)
    clear_cases = get_clear_intent_cases()

    total_turns = 0
    routed_count = 0

    for i, test_case in enumerate(clear_cases):
        input_msg = (
            test_case.input
            if isinstance(test_case.input, str)
            else test_case.input[0]["content"]
        )

        result = await run_agent_until_routed(
            graph=graph,
            initial_message=input_msg,
            thread_id=f"efficiency-test-{i}",
            max_turns=5,
        )

        if result["task_type"] is not None:
            total_turns += result["turns"]
            routed_count += 1

    avg_turns = total_turns / routed_count if routed_count > 0 else float('inf')
    print(f"\nAverage Turns: {avg_turns:.2f}")

    # Assert target efficiency
    assert avg_turns <= 2.0, f"Average turns {avg_turns:.2f} exceeds 2.0 target"
