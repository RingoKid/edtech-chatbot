"""
Activity Planner Node - Graph node that runs the planner agent and extracts output.

Invokes the planner agent and extracts the ActivityPlan from the tool call.
Quality is measured by evals, not runtime validation.
"""

import logging

from langchain_core.messages import AIMessage

logger = logging.getLogger(__name__)

from app.graph.state import GraphState, ActivityPlan
from app.graph.agents.activity_planner import (
    create_activity_planner_agent,
    PLANNER_TOOL_NAME,
)


def _extract_plan(messages: list) -> ActivityPlan | None:
    """Extract ActivityPlan from planner tool call in messages."""
    for msg in reversed(messages):
        if isinstance(msg, AIMessage) and hasattr(msg, 'tool_calls') and msg.tool_calls:
            for tool_call in msg.tool_calls:
                if tool_call.get('name') == PLANNER_TOOL_NAME:
                    args = tool_call.get('args', {})
                    return ActivityPlan(
                        review=args.get('review', ''),
                        sound_target=args.get('sound_target', ''),
                        handwriting=args.get('handwriting', ''),
                        handwriting_chain=args.get('handwriting_chain'),
                        spelling=args.get('spelling', ''),
                        standards=args.get('standards', []),
                        spelling_pattern=args.get('spelling_pattern', 'CVC'),
                        include_directionality=args.get('include_directionality', False),
                        include_articulation=args.get('include_articulation', True),
                        guided_practice_techniques=args.get('guided_practice_techniques', []),
                        scaffolding_intensity=args.get('scaffolding_intensity', 'moderate'),
                        content_scope=args.get('content_scope', ''),
                    )
    return None


async def activity_planner_node(state: GraphState) -> dict:
    """
    Node that runs the activity planner and extracts its output.

    Invokes the planner agent once, extracts the ActivityPlan from
    the tool call, and returns it. No validation or retry — quality
    is measured by evals.
    """
    params = state.get("handwriting_params")
    if params is None:
        return {
            "messages": [AIMessage(content="Error: No handwriting parameters found.")],
        }

    agent = create_activity_planner_agent(
        grade=params["grade"],
        letter=params["letter"],
        student_level=params["student_level"],
        previously_learned=params.get("previously_learned", []),
        skill_focus=params.get("skill_focus", "isolating_sounds"),
    )

    messages = list(state["messages"])
    result = await agent.ainvoke({"messages": messages})
    new_messages = result.get("messages", [])

    plan = _extract_plan(new_messages)
    if plan is None:
        logger.error("Planner did not produce a tool call. Generator will run without activity plan.")

    return {
        "messages": new_messages,
        "activity_plan": plan,
    }
