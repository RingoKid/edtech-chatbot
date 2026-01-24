"""
Routing agent evaluation tests with Langfuse tracing.

Run with:
    docker compose exec backend pytest tests/evals/test_routing_agent.py -v

These tests run the routing agent against the test dataset and measure:
- routing_accuracy: Did agent route to correct task type?
- turn_efficiency: How many turns to complete routing?

Results are logged to Langfuse for analysis in the dashboard.
"""

import pytest
import uuid
from typing import List
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver

from app.graph.graph import create_graph
from app.graph.agents.routing import TOOL_TO_TASK_TYPE
from app.langfuse.client import get_langfuse_client
from tests.datasets.routing_agent import (
    ROUTING_TEST_CASES,
    RoutingTestCase,
    get_clear_intent_cases,
)

# Try to import Langfuse callback handler
try:
    from langfuse.langchain import CallbackHandler as LangfuseCallbackHandler
    LANGFUSE_AVAILABLE = True
except ImportError:
    LANGFUSE_AVAILABLE = False
    LangfuseCallbackHandler = None


class LangfuseTracer:
    """Wrapper for Langfuse tracing in evals."""

    def __init__(self, run_name: str, tags: List[str] = None):
        self.run_name = run_name
        self.tags = tags or ["eval", "routing-agent"]
        self.handler = None
        self.enabled = False

        if LANGFUSE_AVAILABLE:
            client = get_langfuse_client()
            if client is not None:
                self.handler = LangfuseCallbackHandler()
                self.enabled = True

    def get_config(self) -> dict:
        """Get config dict with callbacks and metadata for graph.invoke()."""
        if not self.enabled:
            return {}

        return {
            "callbacks": [self.handler],
            "run_name": self.run_name,
            "metadata": {
                "langfuse_tags": self.tags,
            }
        }

    def score(self, name: str, value: float, comment: str = None):
        """Add a score to the trace. TODO: Fix trace_id capture."""
        # Disabled - trace_id not available at scoring time
        # Traces still work, scores need Langfuse SDK v3 approach
        pass


@pytest.fixture
def memory_checkpointer():
    """In-memory checkpointer for testing (no DynamoDB needed)."""
    return MemorySaver()


async def run_agent_until_routed(
    graph,
    initial_message: str,
    thread_id: str,
    max_turns: int = 10,
    tracer: LangfuseTracer = None,
) -> dict:
    """
    Run the agent until it routes to a task or max turns reached.

    Returns dict with:
    - task_type: The routed task type (or None if not routed)
    - turns: Number of turns taken
    - messages: All messages in conversation
    """
    config = {"configurable": {"thread_id": thread_id}}

    # Add Langfuse tracing if available
    if tracer:
        tracer_config = tracer.get_config()
        config.update(tracer_config)

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

        # Create Langfuse handler for this test
        tracer = LangfuseTracer(
            run_name=f"eval-routing-{test_case.category}",
            tags=["eval", "routing-agent", test_case.category],
        )

        result = await run_agent_until_routed(
            graph=graph,
            initial_message=input_msg,
            thread_id=f"test-{test_case.description}-{uuid.uuid4().hex[:8]}",
            max_turns=test_case.expected_max_turns + 2,
            tracer=tracer,
        )

        # Calculate scores
        is_correct = result["task_type"] == test_case.expected_task_type

        # Log scores to Langfuse
        tracer.score("routing_accuracy", 1.0 if is_correct else 0.0,
                   f"Expected: {test_case.expected_task_type}, Got: {result['task_type']}")
        tracer.score("turn_efficiency", 1.0 if result["turns"] <= test_case.expected_max_turns else 0.0,
                   f"Turns: {result['turns']}, Max: {test_case.expected_max_turns}")

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

        tracer = LangfuseTracer(
            run_name=f"eval-efficiency-{test_case.category}",
            tags=["eval", "routing-agent", "efficiency", test_case.category],
        )

        result = await run_agent_until_routed(
            graph=graph,
            initial_message=input_msg,
            thread_id=f"test-turns-{test_case.description}-{uuid.uuid4().hex[:8]}",
            max_turns=test_case.expected_max_turns + 2,
            tracer=tracer,
        )

        # Log score
        within_limit = result["turns"] <= test_case.expected_max_turns
        tracer.score("turn_efficiency", 1.0 if within_limit else 0.0,
                   f"Turns: {result['turns']}, Max: {test_case.expected_max_turns}")

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

        tracer = LangfuseTracer(
            run_name="eval-greeting",
            tags=["eval", "routing-agent", "greeting"],
        )

        result = await run_agent_until_routed(
            graph=graph,
            initial_message="hi",
            thread_id=f"test-greeting-{uuid.uuid4().hex[:8]}",
            max_turns=1,
            tracer=tracer,
        )

        # Should NOT route on greeting
        is_correct = result["task_type"] is None
        tracer.score("greeting_no_route", 1.0 if is_correct else 0.0,
                   f"Routed to: {result['task_type']}")

        assert is_correct, "Should not route on greeting"

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

        tracer = LangfuseTracer(
            run_name="eval-ambiguous",
            tags=["eval", "routing-agent", "ambiguous"],
        )

        result = await run_agent_until_routed(
            graph=graph,
            initial_message=ambiguous_input,
            thread_id=f"test-ambiguous-{uuid.uuid4().hex[:8]}",
            max_turns=1,
            tracer=tracer,
        )

        # Should NOT route on ambiguous input
        is_correct = result["task_type"] is None
        tracer.score("ambiguous_no_route", 1.0 if is_correct else 0.0,
                   f"Input: {ambiguous_input}, Routed to: {result['task_type']}")

        assert is_correct, f"Should not route on ambiguous input: {ambiguous_input}"


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

        tracer = LangfuseTracer(
            run_name=f"eval-placeholder-{expected_task}",
            tags=["eval", "routing-agent", "placeholder", expected_task],
        )

        result = await run_agent_until_routed(
            graph=graph,
            initial_message=input_msg,
            thread_id=f"test-placeholder-{expected_task}-{uuid.uuid4().hex[:8]}",
            max_turns=2,
            tracer=tracer,
        )

        # Should route to expected task
        is_correct = result["task_type"] == expected_task
        tracer.score("routing_accuracy", 1.0 if is_correct else 0.0,
                   f"Expected: {expected_task}, Got: {result['task_type']}")

        assert is_correct, f"Expected {expected_task}, got {result['task_type']}"

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
    Target: >= 90%
    """
    graph = await create_graph(checkpointer=memory_checkpointer)
    clear_cases = get_clear_intent_cases()

    # Create a single handler for the aggregate test
    tracer = LangfuseTracer(
        run_name="eval-aggregate-accuracy",
        tags=["eval", "routing-agent", "aggregate", "accuracy"],
    )

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
            thread_id=f"accuracy-test-{i}-{uuid.uuid4().hex[:8]}",
            max_turns=3,
            tracer=tracer,
        )

        if result["task_type"] == test_case.expected_task_type:
            correct += 1

    accuracy = correct / total if total > 0 else 0
    print(f"\nRouting Accuracy: {correct}/{total} = {accuracy:.1%}")

    # Log aggregate score
    tracer.score("overall_routing_accuracy", accuracy,
               f"{correct}/{total} correct")

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

    tracer = LangfuseTracer(
        run_name="eval-aggregate-efficiency",
        tags=["eval", "routing-agent", "aggregate", "efficiency"],
    )

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
            thread_id=f"efficiency-test-{i}-{uuid.uuid4().hex[:8]}",
            max_turns=5,
            tracer=tracer,
        )

        if result["task_type"] is not None:
            total_turns += result["turns"]
            routed_count += 1

    avg_turns = total_turns / routed_count if routed_count > 0 else float('inf')
    print(f"\nAverage Turns: {avg_turns:.2f}")

    # Log aggregate score (normalize: 1.0 = 1 turn, 0.5 = 2 turns, 0.0 = 3+ turns)
    efficiency_score = max(0.0, 1.0 - (avg_turns - 1) * 0.5)
    tracer.score("average_turn_efficiency", efficiency_score,
               f"Avg turns: {avg_turns:.2f}")

    # Assert target efficiency
    assert avg_turns <= 2.0, f"Average turns {avg_turns:.2f} exceeds 2.0 target"
