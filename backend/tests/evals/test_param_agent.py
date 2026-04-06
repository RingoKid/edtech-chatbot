"""
Handwriting parameter agent evaluation tests.

Run with:
    docker compose exec backend pytest tests/evals/test_param_agent.py -v

Tests the param agent against multi-turn conversation scenarios:
- Complete extraction (all info in one message)
- Multi-turn extraction (info drip-fed across turns)
- Partial info (should NOT submit)
- Invalid input (should reject)
"""

import pytest
import uuid
from dataclasses import dataclass
from unittest.mock import patch
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver

from app.graph.graph import create_graph
from app.graph.state import HandwritingParams
from app.graph.agents.param import DEFAULT_PARAM_PROMPT
from tests.datasets.param_agent import (
    ParamTestCase,
    get_complete_cases,
    get_multi_turn_cases,
    get_partial_cases,
    get_invalid_cases,
    get_extraction_cases,
)


@dataclass
class TurnResult:
    """Result of a single turn in a multi-turn conversation."""
    message: str
    params: dict | None


def extract_full_params(params: HandwritingParams | None) -> dict | None:
    """Extract all 5 fields from HandwritingParams."""
    if params is None:
        return None
    return {
        "grade": params.get("grade"),
        "letter": params.get("letter"),
        "student_level": params.get("student_level"),
        "previously_learned": params.get("previously_learned"),
        "skill_focus": params.get("skill_focus"),
    }


async def _noop_node(state, *args, **kwargs):
    """No-op replacement for downstream nodes we don't need in param evals."""
    return {}


@pytest.fixture(autouse=True)
def isolate_param_agent():
    """
    Isolate routing + param agent from everything downstream.

    - Forces DEFAULT_PARAM_PROMPT (bypasses stale Langfuse prompt)
    - Mocks activity planner, generator, and image nodes as no-ops
    """
    with (
        patch("app.graph.agents.param.get_param_prompt", return_value=DEFAULT_PARAM_PROMPT),
        patch("app.graph.graph.activity_planner_node", _noop_node),
        patch("app.graph.graph.handwriting_generator_node", _noop_node),
        patch("app.graph.graph.image_assembly_node", _noop_node),
        patch("app.graph.graph.image_director_node", _noop_node),
    ):
        yield


@pytest.fixture
def memory_checkpointer():
    """In-memory checkpointer for testing (no DynamoDB needed)."""
    return MemorySaver()


async def route_to_handwriting(graph, config, max_retries: int = 3) -> bool:
    """
    Route to handwriting task type. Retries with different phrasings.

    Returns True if routing succeeded.
    """
    routing_messages = [
        "I want to create a handwriting lesson",
        "Help me with a letter formation lesson please",
        "handwriting lesson",
    ]

    for attempt, msg in enumerate(routing_messages[:max_retries]):
        retry_thread = (
            config["configurable"]["thread_id"]
            if attempt == 0
            else f"{config['configurable']['thread_id']}-retry{attempt}"
        )
        retry_config = {**config, "configurable": {"thread_id": retry_thread}}

        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=msg)]},
            retry_config,
        )

        if result.get("task_type") == "handwriting":
            # Update config to use the successful thread
            config["configurable"]["thread_id"] = retry_thread
            return True

    return False


async def run_multi_turn_flow(
    graph,
    messages: list[str],
    thread_id: str,
    allow_confirmation: bool = True,
) -> list[TurnResult]:
    """
    Run multi-turn param conversation.

    1. Routes to handwriting (retry up to 3x)
    2. Sends each message sequentially on the same thread
    3. If params still None after last message and allow_confirmation=True,
       sends "yes, that's correct" in case agent asked for confirmation
    4. Returns list of TurnResult (one per message)
    """
    config = {"configurable": {"thread_id": thread_id}}

    # Route to handwriting first
    routed = await route_to_handwriting(graph, config)
    if not routed:
        pytest.skip("Routing to handwriting failed after 3 attempts")

    turns = []
    for msg in messages:
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content=msg)]},
            config,
        )
        params = extract_full_params(result.get("handwriting_params"))
        turns.append(TurnResult(message=msg, params=params))

    # If the agent asked for confirmation instead of submitting, confirm
    if allow_confirmation and turns[-1].params is None:
        result = await graph.ainvoke(
            {"messages": [HumanMessage(content="yes, that's correct")]},
            config,
        )
        params = extract_full_params(result.get("handwriting_params"))
        turns.append(TurnResult(message="yes, that's correct", params=params))

    return turns


def params_match(actual: dict, expected: dict) -> tuple[bool, list[str]]:
    """
    Compare actual vs expected params. Returns (match, mismatches).

    Special handling:
    - previously_learned: compared as sorted sets (order doesn't matter)
    - letter: case-insensitive comparison
    """
    mismatches = []

    for key in expected:
        actual_val = actual.get(key)
        expected_val = expected[key]

        if key == "previously_learned":
            actual_sorted = sorted(s.lower() for s in (actual_val or []))
            expected_sorted = sorted(s.lower() for s in (expected_val or []))
            if actual_sorted != expected_sorted:
                mismatches.append(f"{key}: expected {expected_sorted}, got {actual_sorted}")
        elif key == "letter":
            if (actual_val or "").lower() != (expected_val or "").lower():
                mismatches.append(f"{key}: expected {expected_val!r}, got {actual_val!r}")
        else:
            if actual_val != expected_val:
                mismatches.append(f"{key}: expected {expected_val!r}, got {actual_val!r}")

    return len(mismatches) == 0, mismatches


class TestCompleteExtraction:
    """All info in one message — should submit immediately with all 5 fields correct."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_case",
        get_complete_cases(),
        ids=[tc.description for tc in get_complete_cases()],
    )
    async def test_extracts_correct_params(
        self,
        test_case: ParamTestCase,
        memory_checkpointer,
    ):
        graph = await create_graph(checkpointer=memory_checkpointer)
        thread_id = f"test-complete-{uuid.uuid4().hex[:8]}"

        turns = await run_multi_turn_flow(graph, test_case.messages, thread_id)

        # Should submit on the single turn
        final = turns[-1]
        assert final.params is not None, (
            f"Expected submission but got None.\n"
            f"Input: {test_case.messages[0]}"
        )

        match, mismatches = params_match(final.params, test_case.expected_params)
        assert match, (
            f"Parameter mismatch.\n"
            f"Expected: {test_case.expected_params}\n"
            f"Got: {final.params}\n"
            f"Mismatches: {mismatches}"
        )


class TestMultiTurn:
    """Info spread across turns — should NOT submit until all fields collected."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_case",
        get_multi_turn_cases(),
        ids=[tc.description for tc in get_multi_turn_cases()],
    )
    async def test_multi_turn_submission(
        self,
        test_case: ParamTestCase,
        memory_checkpointer,
    ):
        graph = await create_graph(checkpointer=memory_checkpointer)
        thread_id = f"test-multi-{uuid.uuid4().hex[:8]}"

        turns = await run_multi_turn_flow(graph, test_case.messages, thread_id)

        # All turns before the expected submission should have None params
        submit_idx = test_case.expect_submit_after
        for i, turn in enumerate(turns):
            if i < submit_idx:
                assert turn.params is None, (
                    f"Turn {i} should NOT have submitted yet.\n"
                    f"Message: {turn.message}\n"
                    f"Got params: {turn.params}"
                )

        # Final turn should have correct params
        final = turns[-1]
        assert final.params is not None, (
            f"Expected submission on final turn but got None.\n"
            f"Messages: {test_case.messages}"
        )

        match, mismatches = params_match(final.params, test_case.expected_params)
        assert match, (
            f"Parameter mismatch on final turn.\n"
            f"Expected: {test_case.expected_params}\n"
            f"Got: {final.params}\n"
            f"Mismatches: {mismatches}"
        )


class TestPartialNoSubmit:
    """Partial info only — should ask follow-up, never submit."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_case",
        get_partial_cases(),
        ids=[tc.description for tc in get_partial_cases()],
    )
    async def test_does_not_submit(
        self,
        test_case: ParamTestCase,
        memory_checkpointer,
    ):
        graph = await create_graph(checkpointer=memory_checkpointer)
        thread_id = f"test-partial-{uuid.uuid4().hex[:8]}"

        turns = await run_multi_turn_flow(
            graph, test_case.messages, thread_id, allow_confirmation=False,
        )

        # Should NOT have submitted
        final = turns[-1]
        assert final.params is None, (
            f"Expected NO submission but got params: {final.params}\n"
            f"Input: {test_case.messages[0]}"
        )


class TestInvalid:
    """Invalid input — should reject and ask for correction."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_case",
        get_invalid_cases(),
        ids=[tc.description for tc in get_invalid_cases()],
    )
    async def test_rejects_invalid(
        self,
        test_case: ParamTestCase,
        memory_checkpointer,
    ):
        graph = await create_graph(checkpointer=memory_checkpointer)
        thread_id = f"test-invalid-{uuid.uuid4().hex[:8]}"

        turns = await run_multi_turn_flow(
            graph, test_case.messages, thread_id, allow_confirmation=False,
        )

        # Should NOT have submitted
        final = turns[-1]
        assert final.params is None, (
            f"Expected NO submission for invalid input but got params: {final.params}\n"
            f"Input: {test_case.messages[0]}"
        )


# --- Aggregate Accuracy ---

@pytest.mark.asyncio
async def test_overall_accuracy(memory_checkpointer):
    """
    Run all extraction cases (complete + final turn of multi_turn).
    Target: >= 85%
    """
    graph = await create_graph(checkpointer=memory_checkpointer)
    extraction_cases = get_extraction_cases()

    correct = 0
    total = len(extraction_cases)

    for i, test_case in enumerate(extraction_cases):
        thread_id = f"accuracy-{i}-{uuid.uuid4().hex[:8]}"

        try:
            turns = await run_multi_turn_flow(graph, test_case.messages, thread_id)
            final = turns[-1]

            if final.params is not None and test_case.expected_params is not None:
                match, _ = params_match(final.params, test_case.expected_params)
                if match:
                    correct += 1
        except Exception as e:
            print(f"  Case {i} ({test_case.description}) failed: {e}")

    accuracy = correct / total if total > 0 else 0
    print(f"\nParam Agent Extraction Accuracy: {correct}/{total} = {accuracy:.1%}")

    assert accuracy >= 0.85, (
        f"Param extraction accuracy {accuracy:.1%} below 85% target"
    )
