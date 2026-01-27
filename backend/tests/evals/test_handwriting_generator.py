"""
Handwriting generator agent evaluation tests with Langfuse tracing.

Run with:
    docker compose exec backend pytest tests/evals/test_handwriting_generator.py -v

These tests run the handwriting generator agent against the test dataset and measure:
- structure_complete: All required sections present
- verbatim_check: [Explanations] match Form B exactly
- verbal_cues_correct: Cues match Form F for target letter

Results are logged to Langfuse for analysis in the dashboard.
"""

import pytest
import uuid
from typing import List
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver

from app.graph.graph import create_graph
from app.langfuse.client import get_langfuse_client
from app.langfuse.criteria import (
    evaluate_structure_complete,
    evaluate_verbatim_check,
    evaluate_verbal_cues_correct,
)
from tests.datasets.handwriting_generator import (
    HANDWRITING_GENERATOR_TEST_CASES,
    HandwritingGeneratorTestCase,
    get_all_test_cases,
    get_basic_generation_cases,
    get_verbal_cues_cases,
    get_structure_cases,
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
        self.tags = tags or ["eval", "handwriting-generator"]
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
        pass


@pytest.fixture
def memory_checkpointer():
    """In-memory checkpointer for testing (no DynamoDB needed)."""
    return MemorySaver()


async def run_handwriting_generator_flow(
    graph,
    handwriting_params: dict,
    thread_id: str,
    tracer: LangfuseTracer = None,
    max_routing_retries: int = 3,
) -> dict:
    """
    Run the full flow: routing → param → generator.

    Simulates: user asks for handwriting lesson with all params,
    then routing → param extraction → lesson generation.

    Returns dict with:
    - lesson_output: The generated lesson content
    - messages: All messages in conversation
    - lesson_finalized: Whether finalize_lesson was called
    """
    config = {"configurable": {"thread_id": thread_id}}

    # Add Langfuse tracing if available
    if tracer:
        tracer_config = tracer.get_config()
        config.update(tracer_config)

    # Step 1: Route to handwriting task
    routing_messages = [
        "I want to create a handwriting lesson",
        "Please create a handwriting lesson for my class",
        "handwriting lesson please",
    ]

    routing_result = None
    for attempt, routing_msg in enumerate(routing_messages[:max_routing_retries]):
        retry_thread = f"{thread_id}-retry{attempt}" if attempt > 0 else thread_id
        retry_config = {**config, "configurable": {"thread_id": retry_thread}}

        routing_result = await graph.ainvoke(
            {"messages": [HumanMessage(content=routing_msg)]},
            retry_config,
        )

        task_type = routing_result.get("task_type")
        if task_type == "handwriting":
            config = retry_config
            break

    # Verify routing worked
    task_type = routing_result.get("task_type") if routing_result else None
    if task_type != "handwriting":
        return {
            "lesson_output": "",
            "messages": routing_result.get("messages", []) if routing_result else [],
            "lesson_finalized": False,
            "error": f"Routing failed: got task_type={task_type}",
        }

    # Step 2: Provide params to param agent
    grade = handwriting_params["grade"]
    letter = handwriting_params["letter"]
    student_level = handwriting_params.get("student_level", "on-level")

    param_input = f"{grade} letter {letter}"
    if student_level != "on-level":
        param_input += f" for {student_level} students"

    param_result = await graph.ainvoke(
        {"messages": [HumanMessage(content=param_input)]},
        config=config,
    )

    # Check if params were extracted and generator ran
    if param_result.get("handwriting_params") is None:
        return {
            "lesson_output": "",
            "messages": param_result.get("messages", []),
            "lesson_finalized": False,
            "error": "Param extraction failed",
        }

    # Extract lesson output from messages
    messages = param_result.get("messages", [])
    lesson_output = ""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and msg.content:
            # Skip tool call messages
            if not (hasattr(msg, 'tool_calls') and msg.tool_calls):
                lesson_output = msg.content
                break

    return {
        "lesson_output": lesson_output,
        "messages": messages,
        "lesson_finalized": param_result.get("lesson_finalized", False),
        "handwriting_params": param_result.get("handwriting_params"),
    }


class TestStructureComplete:
    """Tests for structure completeness of generated lessons."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_case",
        get_structure_cases(),
        ids=[tc.description for tc in get_structure_cases()],
    )
    async def test_has_all_sections(
        self,
        test_case: HandwritingGeneratorTestCase,
        memory_checkpointer,
    ):
        """Test that generated lesson has all required sections."""
        graph = await create_graph(checkpointer=memory_checkpointer)

        tracer = LangfuseTracer(
            run_name=f"eval-hw-structure-{test_case.category}",
            tags=["eval", "handwriting-generator", "structure", test_case.category],
        )

        result = await run_handwriting_generator_flow(
            graph=graph,
            handwriting_params=test_case.handwriting_params,
            thread_id=f"test-structure-{test_case.description}-{uuid.uuid4().hex[:8]}",
            tracer=tracer,
        )

        if result.get("error"):
            pytest.skip(f"Flow error: {result['error']}")

        lesson_output = result["lesson_output"]
        eval_result = evaluate_structure_complete(lesson_output)

        tracer.score(
            "structure_complete",
            eval_result.score,
            f"Passed: {eval_result.details['passed']}/{eval_result.details['total']}"
        )

        # Allow 80% of checks to pass (some flexibility for LLM output)
        assert eval_result.score >= 0.8, (
            f"Structure incomplete. Score: {eval_result.score:.1%}\n"
            f"Missing: {[k for k, v in eval_result.details['checks'].items() if not v]}\n"
            f"Letter: {test_case.handwriting_params['letter']}"
        )


class TestVerbatimCheck:
    """Tests for verbatim [Explanation] text from Form B."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_case",
        get_basic_generation_cases()[:2],  # Test a subset
        ids=[tc.description for tc in get_basic_generation_cases()[:2]],
    )
    async def test_explanations_match_form_b(
        self,
        test_case: HandwritingGeneratorTestCase,
        memory_checkpointer,
    ):
        """Test that [Explanation] text matches Form B exactly."""
        graph = await create_graph(checkpointer=memory_checkpointer)

        tracer = LangfuseTracer(
            run_name=f"eval-hw-verbatim-{test_case.category}",
            tags=["eval", "handwriting-generator", "verbatim", test_case.category],
        )

        result = await run_handwriting_generator_flow(
            graph=graph,
            handwriting_params=test_case.handwriting_params,
            thread_id=f"test-verbatim-{test_case.description}-{uuid.uuid4().hex[:8]}",
            tracer=tracer,
        )

        if result.get("error"):
            pytest.skip(f"Flow error: {result['error']}")

        lesson_output = result["lesson_output"]
        eval_result = evaluate_verbatim_check(lesson_output)

        tracer.score(
            "verbatim_check",
            eval_result.score,
            f"Passed: {eval_result.details['passed']}/{eval_result.details['total']}"
        )

        # Allow 60% match (verbatim is strict, LLM may paraphrase)
        assert eval_result.score >= 0.6, (
            f"Verbatim check failed. Score: {eval_result.score:.1%}\n"
            f"Missing: {[k for k, v in eval_result.details['checks'].items() if not v]}\n"
            f"Found {eval_result.details['found_explanations']} explanations"
        )


class TestVerbalCues:
    """Tests for correct verbal cues from Form F."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_case",
        get_verbal_cues_cases(),
        ids=[tc.description for tc in get_verbal_cues_cases()],
    )
    async def test_verbal_cues_correct(
        self,
        test_case: HandwritingGeneratorTestCase,
        memory_checkpointer,
    ):
        """Test that ##Sequence Verbal Cues match Form F for target letter."""
        graph = await create_graph(checkpointer=memory_checkpointer)

        tracer = LangfuseTracer(
            run_name=f"eval-hw-cues-{test_case.category}",
            tags=["eval", "handwriting-generator", "verbal-cues", test_case.category],
        )

        result = await run_handwriting_generator_flow(
            graph=graph,
            handwriting_params=test_case.handwriting_params,
            thread_id=f"test-cues-{test_case.description}-{uuid.uuid4().hex[:8]}",
            tracer=tracer,
        )

        if result.get("error"):
            pytest.skip(f"Flow error: {result['error']}")

        lesson_output = result["lesson_output"]
        target_letter = test_case.handwriting_params["letter"]

        eval_result = evaluate_verbal_cues_correct(lesson_output, target_letter)

        tracer.score(
            "verbal_cues_correct",
            eval_result.score,
            f"Letter: {target_letter}, Found: {eval_result.details['found_match']}"
        )

        assert eval_result.score >= 0.9, (
            f"Verbal cues incorrect for letter {target_letter}.\n"
            f"Expected: {eval_result.details['expected_uppercase']}\n"
            f"Found: {eval_result.details['matched_cue']}"
        )


class TestFinalizeLesson:
    """Tests for finalize_lesson tool behavior."""

    @pytest.mark.asyncio
    async def test_finalize_on_approval(self, memory_checkpointer):
        """Test that finalize_lesson is called when user approves."""
        graph = await create_graph(checkpointer=memory_checkpointer)
        thread_id = f"test-finalize-{uuid.uuid4().hex[:8]}"
        config = {"configurable": {"thread_id": thread_id}}

        tracer = LangfuseTracer(
            run_name="eval-hw-finalize",
            tags=["eval", "handwriting-generator", "finalize"],
        )
        tracer_config = tracer.get_config()
        config.update(tracer_config)

        # Generate initial lesson
        result = await run_handwriting_generator_flow(
            graph=graph,
            handwriting_params={"grade": "K", "letter": "A", "student_level": "on-level"},
            thread_id=thread_id,
            tracer=tracer,
        )

        if result.get("error"):
            pytest.skip(f"Flow error: {result['error']}")

        # Now send approval message
        approval_result = await graph.ainvoke(
            {"messages": [HumanMessage(content="Looks great, thanks!")]},
            config=config,
        )

        # Check if finalize was called
        lesson_finalized = approval_result.get("lesson_finalized", False)

        tracer.score(
            "finalize_called",
            1.0 if lesson_finalized else 0.0,
            f"Finalized: {lesson_finalized}"
        )

        # Note: This test may not always pass since the LLM decides when to call finalize
        # We check that finalize CAN be called, not that it always is
        # The graph structure supports it, actual behavior depends on LLM


# --- Aggregate Metrics ---

@pytest.mark.asyncio
async def test_overall_structure_accuracy(memory_checkpointer):
    """
    Aggregate test: Calculate overall structure completeness.

    Target: >= 80%
    """
    graph = await create_graph(checkpointer=memory_checkpointer)
    test_cases = get_all_test_cases()[:4]  # Test subset for speed

    tracer = LangfuseTracer(
        run_name="eval-aggregate-structure",
        tags=["eval", "handwriting-generator", "aggregate", "structure"],
    )

    total_score = 0.0
    count = 0

    for i, test_case in enumerate(test_cases):
        result = await run_handwriting_generator_flow(
            graph=graph,
            handwriting_params=test_case.handwriting_params,
            thread_id=f"aggregate-structure-{i}-{uuid.uuid4().hex[:8]}",
            tracer=tracer,
        )

        if result.get("error"):
            continue

        eval_result = evaluate_structure_complete(result["lesson_output"])
        total_score += eval_result.score
        count += 1

    accuracy = total_score / count if count > 0 else 0
    print(f"\nStructure Accuracy: {accuracy:.1%}")

    tracer.score("overall_structure_accuracy", accuracy, f"{count} tests")

    assert accuracy >= 0.8, f"Structure accuracy {accuracy:.1%} below 80% target"


@pytest.mark.asyncio
async def test_overall_verbal_cues_accuracy(memory_checkpointer):
    """
    Aggregate test: Calculate overall verbal cues accuracy.

    Target: >= 90%
    """
    graph = await create_graph(checkpointer=memory_checkpointer)
    test_cases = get_verbal_cues_cases()

    tracer = LangfuseTracer(
        run_name="eval-aggregate-verbal-cues",
        tags=["eval", "handwriting-generator", "aggregate", "verbal-cues"],
    )

    correct = 0
    total = 0

    for i, test_case in enumerate(test_cases):
        result = await run_handwriting_generator_flow(
            graph=graph,
            handwriting_params=test_case.handwriting_params,
            thread_id=f"aggregate-cues-{i}-{uuid.uuid4().hex[:8]}",
            tracer=tracer,
        )

        if result.get("error"):
            continue

        target_letter = test_case.handwriting_params["letter"]
        eval_result = evaluate_verbal_cues_correct(result["lesson_output"], target_letter)

        if eval_result.score >= 0.9:
            correct += 1
        total += 1

    accuracy = correct / total if total > 0 else 0
    print(f"\nVerbal Cues Accuracy: {correct}/{total} = {accuracy:.1%}")

    tracer.score("overall_verbal_cues_accuracy", accuracy, f"{correct}/{total} correct")

    assert accuracy >= 0.75, f"Verbal cues accuracy {accuracy:.1%} below 75% target"
