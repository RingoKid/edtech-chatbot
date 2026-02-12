"""
Feedback collector node-level evaluation tests.

Run with:
    docker compose exec backend pytest tests/evals/test_feedback_collector.py -v

These tests invoke the feedback collector agent directly and verify tool calls.
"""

import pytest
import uuid
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage
from langgraph.checkpoint.memory import MemorySaver

from app.graph.agents.feedback_collector import (
    create_feedback_collector_agent,
    SUBMIT_FEEDBACK_TOOL_NAME,
    SKIP_FEEDBACK_TOOL_NAME,
)


def extract_tool_call(result: dict) -> dict | None:
    """
    Extract the first feedback-related tool call from agent result messages.

    Returns dict with 'name' and 'args', or None if no tool called.
    """
    messages = result.get("messages", [])
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tc in msg.tool_calls:
                if tc.get('name') in (SUBMIT_FEEDBACK_TOOL_NAME, SKIP_FEEDBACK_TOOL_NAME):
                    return tc
    return None


async def run_feedback_agent(user_message: str, include_finalize_context: bool = True):
    """
    Run the feedback collector agent with a user message.

    If include_finalize_context is True, prepends context messages
    that simulate a lesson having been finalized.
    """
    agent = create_feedback_collector_agent()

    messages = []
    if include_finalize_context:
        # Simulate the conversation context: user said "looks good" to generator
        messages.append(HumanMessage(content="Looks good, thanks!"))
        messages.append(AIMessage(content=(
            "Great! Your lesson has been finalized. "
            "Before we wrap up, do you have any feedback about the lesson "
            "or the platform? You can also say 'skip' to finish."
        )))

    messages.append(HumanMessage(content=user_message))

    result = agent.invoke({"messages": messages})
    return result


class TestFeedbackToolCalls:
    """Tests that the feedback collector calls the right tools."""

    @pytest.mark.asyncio
    async def test_positive_feedback(self):
        """Positive lesson feedback → submit_feedback with category='lesson'."""
        result = await run_feedback_agent("Great lesson!")

        tc = extract_tool_call(result)
        assert tc is not None, "Expected submit_feedback to be called"
        assert tc['name'] == SUBMIT_FEEDBACK_TOOL_NAME
        assert tc['args'].get('category') == 'lesson'

    @pytest.mark.asyncio
    async def test_platform_feedback(self):
        """Platform-related feedback → submit_feedback with category='platform'."""
        result = await run_feedback_agent("App is slow")

        tc = extract_tool_call(result)
        assert tc is not None, "Expected submit_feedback to be called"
        assert tc['name'] == SUBMIT_FEEDBACK_TOOL_NAME
        assert tc['args'].get('category') == 'platform'

    @pytest.mark.asyncio
    async def test_skip_feedback(self):
        """Decline feedback → skip_feedback called."""
        result = await run_feedback_agent("No thanks")

        tc = extract_tool_call(result)
        assert tc is not None, "Expected skip_feedback to be called"
        assert tc['name'] == SKIP_FEEDBACK_TOOL_NAME

    @pytest.mark.asyncio
    async def test_rating_extracted(self):
        """Explicit rating → extracted as integer."""
        result = await run_feedback_agent("5 stars, amazing lesson!")

        tc = extract_tool_call(result)
        assert tc is not None, "Expected submit_feedback to be called"
        assert tc['name'] == SUBMIT_FEEDBACK_TOOL_NAME
        assert tc['args'].get('rating') == 5

    @pytest.mark.asyncio
    async def test_no_rating_defaults_zero(self):
        """No rating mentioned → rating=0."""
        result = await run_feedback_agent("The lesson was well structured and easy to follow")

        tc = extract_tool_call(result)
        assert tc is not None, "Expected submit_feedback to be called"
        assert tc['name'] == SUBMIT_FEEDBACK_TOOL_NAME
        assert tc['args'].get('rating') == 0
