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
    Note: This is the old placeholder before param collection was added.
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


def handwriting_generator_placeholder(state: GraphState) -> dict:
    """
    Placeholder for handwriting generator (after param collection).

    Shows the collected parameters to confirm extraction worked.
    Will be replaced by actual generator in spec 012.
    """
    params = state.get("handwriting_params")

    if params:
        content = (
            f"**Handwriting Lesson Generator** - Coming Soon!\n\n"
            f"I've collected your lesson parameters:\n"
            f"- **Grade Level:** {params['grade']}\n"
            f"- **Letter:** {params['letter']}\n"
            f"- **Student Level:** {params['student_level']}\n\n"
            f"The full lesson generator is coming in the next update. "
            f"Check back soon!"
        )
    else:
        content = (
            "**Handwriting Lesson Generator** - Coming Soon!\n\n"
            "Something went wrong - no parameters were collected. "
            "Please try again."
        )

    message = AIMessage(content=content)
    return {
        "messages": [message],
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


def vocabulary_generator_placeholder(state: GraphState) -> dict:
    """
    Placeholder for vocabulary generator (after param collection).

    Shows the collected parameters to confirm extraction worked.
    Will be replaced by actual generator in a future spec.
    """
    params = state.get("vocabulary_params")

    if params:
        vocab_list = ", ".join(params.get('key_vocabulary', []))
        content = (
            f"**Vocabulary Lesson Generator** - Coming Soon!\n\n"
            f"I've collected your lesson parameters:\n"
            f"- **Grade Level:** {params['grade']}\n"
            f"- **Writing Type:** {params['writing_type']}\n"
            f"- **Key Vocabulary:** {vocab_list}\n"
            f"- **Objectives:** {params['objectives']}\n"
            f"- **Student Level:** {params['student_level']}\n\n"
            f"The full lesson generator is coming in the next update. "
            f"Check back soon!"
        )
    else:
        content = (
            "**Vocabulary Lesson Generator** - Coming Soon!\n\n"
            "Something went wrong - no parameters were collected. "
            "Please try again."
        )

    message = AIMessage(content=content)
    return {
        "messages": [message],
    }


def idea_generation_generator_placeholder(state: GraphState) -> dict:
    """
    Placeholder for idea generation generator (after param collection).

    Shows the collected parameters to confirm extraction worked.
    Will be replaced by actual generator in a future spec.
    """
    params = state.get("idea_generation_params")

    if params:
        content = (
            f"**Idea Generation Lesson Generator** - Coming Soon!\n\n"
            f"I've collected your lesson parameters:\n"
            f"- **Grade Level:** {params['grade']}\n"
            f"- **Genre:** {params['genre']}\n"
            f"- **Genre Component:** {params['genre_component']}\n"
            f"- **Writing Stage:** {params['writing_stage']}\n"
            f"- **Objectives:** {params['objectives']}\n"
            f"- **Student Level:** {params['student_level']}\n\n"
            f"The full lesson generator is coming in the next update. "
            f"Check back soon!"
        )
    else:
        content = (
            "**Idea Generation Lesson Generator** - Coming Soon!\n\n"
            "Something went wrong - no parameters were collected. "
            "Please try again."
        )

    message = AIMessage(content=content)
    return {
        "messages": [message],
    }
