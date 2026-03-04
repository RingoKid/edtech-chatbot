"""
Image director node — extracts image descriptions from lesson markdown + fires off generation.

1. Reads the completed lesson markdown (with S3 URLs already replaced by assembly)
2. Extracts image descriptions from ![desc](https://...l4c-videos...) patterns
3. Prepends style suffix to each description as the Gemini prompt
4. Fires off Gemini image generation in the background (non-blocking)
"""

import logging
import re

from langchain_core.runnables import RunnableConfig

from app.graph.state import GraphState

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())

STYLE_SUFFIX = (
    " Clean, simple, rounded children's book illustration style. "
    "On a pure white background with no border, designed for printing "
    "on standard white paper. Age-appropriate for early childhood (PreK-1st grade). "
    "Bright but not neon colors, simple rounded shapes, maximum 3-4 objects."
)


def _extract_image_descriptions(markdown: str) -> list[dict]:
    """Extract image descriptions and URLs from markdown with S3 image links.

    Parses patterns like:
        ![Some pedagogical description](https://l4c-videos.s3.amazonaws.com/images/...)

    Returns list of dicts with {prompt, alt_text} for each match.
    """
    pattern = r"!\[([^\]]+)\]\((https://l4c-videos\.s3\.amazonaws\.com/[^)]+)\)"
    matches = re.findall(pattern, markdown)

    results = []
    for alt_text, url in matches:
        results.append({
            "prompt": alt_text.strip() + STYLE_SUFFIX,
            "alt_text": alt_text.strip(),
        })

    return results


def _extract_lesson_markdown(state: GraphState) -> str:
    """Read lesson markdown from state (set by image_assembly_node)."""
    return state.get("lesson_markdown") or ""


async def _background_generate_images(image_requests: list[dict], thread_id: str):
    """Fire-and-forget: generate images and upload to S3 in the background."""
    # Lazy import to avoid circular import: graph → nodes → services → chat_service → graph
    from app.services.image_service import generate_all

    try:
        logger.info(f"Image director (background): generating {len(image_requests)} images")
        image_results = await generate_all(image_requests, thread_id)
        logger.info(f"Image director (background): all {len(image_results)} images uploaded")
    except Exception as e:
        logger.error(f"Background image generation failed: {e}")


async def image_director_node(state: GraphState, config: RunnableConfig) -> dict:
    """
    Image director: extract descriptions from markdown, kick off generation.

    This node:
    1. Reads lesson markdown (with S3 URLs already in place from assembly)
    2. Extracts image descriptions via regex
    3. Prepends STYLE_SUFFIX to each as the Gemini prompt
    4. Kicks off Gemini image generation as a background task (non-blocking)
    5. Returns image_requests to state

    No LLM call needed — the generator already placed descriptive placeholders.
    """
    thread_id = config.get("configurable", {}).get("thread_id", "unknown")

    lesson_markdown = _extract_lesson_markdown(state)

    if not lesson_markdown:
        logger.warning("No lesson markdown found in state — skipping image generation")
        return {"image_requests": None}

    # Extract descriptions from the already-replaced markdown
    image_requests = _extract_image_descriptions(lesson_markdown)

    if not image_requests:
        logger.warning("No image placeholders found in lesson markdown")
        return {"image_requests": None}

    logger.info(f"Image director: extracted {len(image_requests)} image descriptions for thread {thread_id}")

    # Fire-and-forget background task for Gemini generation + S3 upload
    import asyncio
    asyncio.create_task(_background_generate_images(image_requests, thread_id))

    return {
        "image_requests": image_requests,
    }
