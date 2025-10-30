from __future__ import annotations

import logging
from typing import Any, Dict

from app.core.context import Context
from app.graph.state import GraphState
from app.schemas.lesson_output import LESSON_SCHEMA_REGISTRY
from app.services.model_utils import safe_structured_invoke
from app.services.prompt_builder import PromptBuilder


logger = logging.getLogger(__name__)


def _append_message(state: GraphState, content: str) -> None:
    msgs = state.get("messages") or []
    msgs.append({"role": "ai", "content": content})
    state["messages"] = msgs


def generate_lesson_node(state: GraphState) -> Dict[str, Any]:
    """Generates a structured lesson plan from collected parameters."""
    task_name = state.get("task_name")
    collected_params = state.get("collected_parameters", {})

    logger.debug("generate_lesson_node: task=%s params=%s", task_name, collected_params)

    if not task_name:
        _append_message(state, "Missing task. Please choose a task (Handwriting, Vocabulary, Idea Generation).")
        return state

    try:
        builder = PromptBuilder(task_name, collected_params)
        lesson_prompt = builder.build_prompt()
        metadata = builder.get_metadata()

        logger.info("Prompt built for task=%s; forms=%s", task_name, metadata.get("forms_used"))

        context = Context()

        model = context.get_model(task_name, collected_params.get("query_type"), demand="balanced")
        lesson_schema = LESSON_SCHEMA_REGISTRY.get(task_name)
        if not lesson_schema:
            raise ValueError(f"No lesson schema found for task: {task_name}")

        lesson_obj = safe_structured_invoke(model, lesson_schema, lesson_prompt, strict=False)

        # Coerce to dict if it's a pydantic model
        try:
            lesson_dict = lesson_obj.model_dump()  # type: ignore[attr-defined]
        except Exception:
            lesson_dict = dict(lesson_obj) if isinstance(lesson_obj, dict) else {"content": str(lesson_obj)}

        display_content = _format_lesson_for_display(lesson_dict, task_name)

        state.update({
            "generated_lesson": lesson_dict,
            "prompt_metadata": metadata,
        })
        _append_message(state, display_content)
        return state

    except Exception as e:
        logger.exception("Error in generate_lesson_node: %s", e)
        _append_message(state, f"Error generating lesson: {e}. Please try again.")
        return state


def _format_lesson_for_display(lesson: Dict[str, Any], task_name: str) -> str:
    lines = [
        f"# {lesson.get('lesson_title', 'Lesson Plan')}",
        "",
        f"**Grade Level:** {lesson.get('target_grade')}",
        f"**Focus Area:** {lesson.get('query_type')}",
        "",
    ]

    if task_name == "Handwriting" and lesson.get("target_letters"):
        lines.append(f"**Target Letters:** {lesson['target_letters']}")
        lines.append("")
    elif task_name == "Vocabulary":
        if lesson.get("target_vocabulary"):
            lines.append(f"**Target Vocabulary:** {lesson['target_vocabulary']}")
        if lesson.get("target_genre"):
            lines.append(f"**Genre:** {lesson['target_genre']}")
        lines.append("")
    elif task_name == "Idea Generation":
        lines.append(f"**Genre:** {lesson.get('target_genre')}")
        lines.append(f"**Topic:** {lesson.get('target_topic')}")
        lines.append("")

    lines.extend([
        "## Standards",
        lesson.get("standards", "N/A"),
        "",
        "## Objectives",
        lesson.get("objectives", "N/A"),
        "",
        "## Materials",
        lesson.get("materials", "N/A"),
        "",
        "## Lesson Plan",
        "",
    ])

    section_map = {
        "review_connect": "Review & Connect",
        "model_explain_engage": "Model, Explain & Engage",
        "guided_practice": "Guided Practice",
        "application": "Application",
        "wrap_up": "Wrap-Up",
    }

    for key, title in section_map.items():
        if lesson.get(key):
            lines.extend([f"### {title}", lesson[key], ""])  # type: ignore[index]

    lines.append("---")
    lines.append("*Lesson plan generated successfully. You can now use this with your students!*")
    return "\n".join(lines)


