"""
Vocabulary parameter agent evaluation tests with Langfuse tracing.

Run with:
    docker compose exec backend pytest tests/evals/test_vocab_params.py -v

These tests run the param agent against the vocabulary test dataset and measure:
- vocab_param_extraction_accuracy: Did agent extract correct parameters?

Results are logged to Langfuse for analysis in the dashboard.
"""

import pytest
import uuid
from typing import List
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver

from app.graph.graph import create_graph
from app.graph.state import VocabularySyntaxParams
from app.langfuse.client import get_langfuse_client
from app.langfuse.criteria import evaluate_vocab_param_extraction_accuracy
from tests.datasets.vocab_params import (
    VOCAB_TEST_CASES,
    VocabParamTestCase,
    get_extraction_cases,
    get_clarification_cases,
    get_all_test_cases,
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
        self.tags = tags or ["eval", "vocab-params"]
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


async def run_vocab_param_agent_flow(
    graph,
    user_input: str,
    thread_id: str,
    tracer: LangfuseTracer = None,
    max_routing_retries: int = 3,
) -> dict:
    """
    Run the full flow: routing agent routes to vocabulary, then param agent.

    Simulates: user says "vocabulary" -> routed -> user provides params

    Returns dict with:
    - vocabulary_params: Extracted params (or None)
    - messages: All messages in conversation
    - task_type: The task type after routing
    """
    config = {"configurable": {"thread_id": thread_id}}

    # Add Langfuse tracing if available
    if tracer:
        tracer_config = tracer.get_config()
        config.update(tracer_config)

    # Retry routing since LLM can be non-deterministic
    routing_messages = [
        "I want to create a vocabulary lesson",
        "Please help me with a vocabulary and sentence structure lesson",
        "vocabulary lesson please",
    ]

    routing_result = None
    for attempt, routing_msg in enumerate(routing_messages[:max_routing_retries]):
        # Use fresh thread for each retry attempt
        retry_thread = f"{thread_id}-retry{attempt}" if attempt > 0 else thread_id
        retry_config = {**config, "configurable": {"thread_id": retry_thread}}

        routing_result = await graph.ainvoke(
            {"messages": [HumanMessage(content=routing_msg)]},
            retry_config,
        )

        task_type = routing_result.get("task_type")
        if task_type == "vocabulary":
            # Success! Continue with this thread
            config = retry_config
            break

    # Verify routing worked after retries
    task_type = routing_result.get("task_type") if routing_result else None
    if task_type != "vocabulary":
        return {
            "vocabulary_params": None,
            "messages": routing_result.get("messages", []) if routing_result else [],
            "task_type": task_type,
            "error": f"Routing failed after {max_routing_retries} attempts: got task_type={task_type}",
        }

    # Now continue the conversation with the param input
    param_result = await graph.ainvoke(
        {"messages": [HumanMessage(content=user_input)]},
        config=config,
    )

    return {
        "vocabulary_params": param_result.get("vocabulary_params"),
        "messages": param_result.get("messages", []),
        "task_type": param_result.get("task_type"),
    }


def params_to_dict(params: VocabularySyntaxParams | None) -> dict | None:
    """Convert VocabularySyntaxParams to dict for comparison."""
    if params is None:
        return None
    return {
        "grade": params.get("grade"),
        "writing_type": params.get("writing_type"),
        "key_vocabulary": params.get("key_vocabulary", []),
        "objectives": params.get("objectives"),
        "student_level": params.get("student_level"),
    }


class TestVocabParamExtraction:
    """Tests for vocabulary parameter extraction on cases where extraction is expected."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_case",
        get_extraction_cases(),
        ids=[tc.description for tc in get_extraction_cases()],
    )
    async def test_extracts_correct_params(
        self,
        test_case: VocabParamTestCase,
        memory_checkpointer,
    ):
        """Test that agent extracts correct vocabulary parameters."""
        graph = await create_graph(checkpointer=memory_checkpointer)

        input_msg = (
            test_case.input
            if isinstance(test_case.input, str)
            else test_case.input[0]["content"]
        )

        tracer = LangfuseTracer(
            run_name=f"eval-vocab-{test_case.category}",
            tags=["eval", "vocab-params", test_case.category],
        )

        result = await run_vocab_param_agent_flow(
            graph=graph,
            user_input=input_msg,
            thread_id=f"test-vocab-{test_case.description}-{uuid.uuid4().hex[:8]}",
            tracer=tracer,
        )

        # Convert params to dict for comparison
        actual_params = params_to_dict(result["vocabulary_params"])
        expected_params = test_case.expected_params

        # Evaluate
        eval_result = evaluate_vocab_param_extraction_accuracy(actual_params, expected_params)

        tracer.score(
            "vocab_param_extraction_accuracy",
            eval_result.score,
            f"Expected: {expected_params}, Got: {actual_params}"
        )

        # Assert correct extraction
        assert eval_result.score == 1.0, (
            f"Vocabulary parameter extraction failed.\n"
            f"Expected: {expected_params}\n"
            f"Got: {actual_params}\n"
            f"Input: {input_msg}\n"
            f"Mismatches: {eval_result.details.get('mismatches', [])}"
        )


class TestVocabClarification:
    """Tests for clarification on cases where extraction should NOT happen."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_case",
        get_clarification_cases(),
        ids=[tc.description for tc in get_clarification_cases()],
    )
    async def test_asks_for_clarification(
        self,
        test_case: VocabParamTestCase,
        memory_checkpointer,
    ):
        """Test that agent asks for clarification when info is missing/invalid."""
        graph = await create_graph(checkpointer=memory_checkpointer)

        input_msg = (
            test_case.input
            if isinstance(test_case.input, str)
            else test_case.input[0]["content"]
        )

        tracer = LangfuseTracer(
            run_name=f"eval-vocab-clarify-{test_case.category}",
            tags=["eval", "vocab-params", "clarification", test_case.category],
        )

        result = await run_vocab_param_agent_flow(
            graph=graph,
            user_input=input_msg,
            thread_id=f"test-vocab-clarify-{test_case.description}-{uuid.uuid4().hex[:8]}",
            tracer=tracer,
        )

        # Should NOT extract params (should ask for clarification)
        actual_params = params_to_dict(result["vocabulary_params"])

        is_correct = actual_params is None
        tracer.score(
            "vocab_clarification_correct",
            1.0 if is_correct else 0.0,
            f"Expected no extraction, got: {actual_params}"
        )

        assert is_correct, (
            f"Expected clarification (no extraction), but got params: {actual_params}\n"
            f"Input: {input_msg}"
        )

        # Should have an AI response (asking for more info)
        ai_messages = [
            m for m in result["messages"]
            if isinstance(m, AIMessage) and m.content
        ]
        assert len(ai_messages) > 0, "Should have AI response asking for clarification"


class TestVocabGeneratorPlaceholder:
    """Tests that generator placeholder shows params after extraction."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "test_case",
        get_extraction_cases()[:3],  # Just test a few
        ids=[tc.description for tc in get_extraction_cases()[:3]],
    )
    async def test_placeholder_shows_params(
        self,
        test_case: VocabParamTestCase,
        memory_checkpointer,
    ):
        """Test that generator placeholder shows collected params."""
        graph = await create_graph(checkpointer=memory_checkpointer)

        input_msg = (
            test_case.input
            if isinstance(test_case.input, str)
            else test_case.input[0]["content"]
        )

        tracer = LangfuseTracer(
            run_name=f"eval-vocab-placeholder",
            tags=["eval", "vocab-params", "placeholder"],
        )

        result = await run_vocab_param_agent_flow(
            graph=graph,
            user_input=input_msg,
            thread_id=f"test-vocab-placeholder-{test_case.description}-{uuid.uuid4().hex[:8]}",
            tracer=tracer,
        )

        # Should have params
        assert result["vocabulary_params"] is not None, "Params should be extracted"

        # Check for "Coming Soon" in messages (from placeholder)
        messages = result.get("messages", [])
        ai_messages = [m for m in messages if isinstance(m, AIMessage)]

        found_coming_soon = any(
            "coming soon" in m.content.lower()
            for m in ai_messages
            if m.content
        )
        assert found_coming_soon, "Expected 'Coming Soon' from generator placeholder"


# --- Aggregate Metrics ---

@pytest.mark.asyncio
async def test_overall_vocab_param_extraction_accuracy(memory_checkpointer):
    """
    Aggregate test: Calculate overall vocabulary param extraction accuracy.

    This test runs all extraction cases and reports overall accuracy.
    Target: >= 85%
    """
    graph = await create_graph(checkpointer=memory_checkpointer)
    extraction_cases = get_extraction_cases()

    tracer = LangfuseTracer(
        run_name="eval-aggregate-vocab-accuracy",
        tags=["eval", "vocab-params", "aggregate", "accuracy"],
    )

    correct = 0
    total = len(extraction_cases)

    for i, test_case in enumerate(extraction_cases):
        input_msg = (
            test_case.input
            if isinstance(test_case.input, str)
            else test_case.input[0]["content"]
        )

        result = await run_vocab_param_agent_flow(
            graph=graph,
            user_input=input_msg,
            thread_id=f"accuracy-vocab-{i}-{uuid.uuid4().hex[:8]}",
            tracer=tracer,
        )

        actual_params = params_to_dict(result["vocabulary_params"])
        expected_params = test_case.expected_params

        eval_result = evaluate_vocab_param_extraction_accuracy(actual_params, expected_params)
        if eval_result.score == 1.0:
            correct += 1

    accuracy = correct / total if total > 0 else 0
    print(f"\nVocab Param Extraction Accuracy: {correct}/{total} = {accuracy:.1%}")

    tracer.score("overall_vocab_accuracy", accuracy, f"{correct}/{total} correct")

    # Assert target accuracy
    assert accuracy >= 0.85, f"Vocab param extraction accuracy {accuracy:.1%} below 85% target"


@pytest.mark.asyncio
async def test_overall_vocab_clarification_accuracy(memory_checkpointer):
    """
    Aggregate test: Calculate accuracy of asking for clarification.

    Target: >= 80% (invalid/missing cases can be tricky)
    """
    graph = await create_graph(checkpointer=memory_checkpointer)
    clarification_cases = get_clarification_cases()

    tracer = LangfuseTracer(
        run_name="eval-aggregate-vocab-clarification",
        tags=["eval", "vocab-params", "aggregate", "clarification"],
    )

    correct = 0
    total = len(clarification_cases)

    for i, test_case in enumerate(clarification_cases):
        input_msg = (
            test_case.input
            if isinstance(test_case.input, str)
            else test_case.input[0]["content"]
        )

        result = await run_vocab_param_agent_flow(
            graph=graph,
            user_input=input_msg,
            thread_id=f"clarify-vocab-{i}-{uuid.uuid4().hex[:8]}",
            tracer=tracer,
        )

        actual_params = params_to_dict(result["vocabulary_params"])
        # Should be None for clarification cases
        if actual_params is None:
            correct += 1

    accuracy = correct / total if total > 0 else 0
    print(f"\nVocab Clarification Accuracy: {correct}/{total} = {accuracy:.1%}")

    tracer.score("overall_vocab_clarification_accuracy", accuracy, f"{correct}/{total} correct")

    # More lenient threshold - invalid inputs can be tricky
    assert accuracy >= 0.80, f"Vocab clarification accuracy {accuracy:.1%} below 80% target"
