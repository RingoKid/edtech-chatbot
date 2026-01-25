"""
Placeholder nodes for task agents.

These nodes are temporary stubs that will be replaced by real task agents
in future specs (012, 014, 015). They confirm routing worked correctly
during development.
"""

from langchain_core.messages import AIMessage

from app.graph.state import GraphState


def handwriting_placeholder(state: GraphState) -> dict:
    """
    Placeholder for handwriting task agent.

    Will be replaced by spec 012 implementation.
    """
    message = AIMessage(
        content=(
            "**Handwriting Lesson Creator** - Coming Soon!\n\n"
            "This feature will help you create handwriting lessons for letter formation, "
            "tracing practice, and fine motor skill development.\n\n"
            "Check back soon for the full experience!"
        )
    )
    return {
        "messages": [message],
        "routing_complete": True,
    }


def vocabulary_placeholder(state: GraphState) -> dict:
    """
    Placeholder for vocabulary task agent.

    Will be replaced by spec 014 implementation.
    """
    message = AIMessage(
        content=(
            "**Vocabulary Lesson Creator** - Coming Soon!\n\n"
            "This feature will help you build vocabulary lessons with word lists, "
            "definitions, and engaging activities for your students.\n\n"
            "Check back soon for the full experience!"
        )
    )
    return {
        "messages": [message],
        "routing_complete": True,
    }


def idea_generation_placeholder(state: GraphState) -> dict:
    """
    Placeholder for idea generation task agent.

    Will be replaced by spec 015 implementation.
    """
    message = AIMessage(
        content=(
            "**Lesson Idea Generator** - Coming Soon!\n\n"
            "This feature will help you brainstorm creative lesson ideas, "
            "activity suggestions, and teaching approaches.\n\n"
            "Check back soon for the full experience!"
        )
    )
    return {
        "messages": [message],
        "routing_complete": True,
    }
