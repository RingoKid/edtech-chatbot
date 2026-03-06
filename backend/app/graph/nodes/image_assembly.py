"""
Image assembly node — computes pre-known S3 URLs and replaces tokens in lesson markdown.

This is a pure function (no LLM call). It runs after the handwriting
generator finalizes a lesson, computing URLs that the frontend can
reference immediately as placeholders while images generate async.
"""

import re

from langchain_core.runnables import RunnableConfig

from app.graph.state import GraphState

# Constants duplicated here to avoid circular import through services/__init__.py
_S3_BUCKET = "l4c-videos"
_S3_URL_PREFIX = f"https://{_S3_BUCKET}.s3.amazonaws.com"
_NUM_IMAGES = 3


def _compute_image_urls(thread_id: str, count: int = _NUM_IMAGES) -> list[str]:
    """Compute pre-known S3 URLs for lesson images."""
    return [
        f"{_S3_URL_PREFIX}/images/{thread_id}/img_{n}.jpg"
        for n in range(1, count + 1)
    ]


def _replace_image_tokens(markdown: str, image_urls: list[str]) -> str:
    """Replace IMAGE_N tokens in markdown with actual S3 URLs.

    Handles tokens inside markdown image syntax like:
        ![description](IMAGE_1) → ![description](https://...img_1.jpg)
    """
    result = markdown
    for i, url in enumerate(image_urls, start=1):
        result = result.replace(f"IMAGE_{i}", url)
    return result


def image_assembly_node(state: GraphState, config: RunnableConfig) -> dict:
    """
    Compute pre-known S3 URLs, replace IMAGE_N tokens in lesson markdown.

    Reads thread_id from the RunnableConfig (set by ChatService when
    invoking the graph). Produces 3 URLs at:
        images/{thread_id}/img_{1,2,3}.jpg

    Also replaces IMAGE_1/2/3 tokens in lesson_markdown with the actual
    S3 URLs so the markdown contains final image references.
    """
    thread_id = config.get("configurable", {}).get("thread_id", "unknown")
    image_urls = _compute_image_urls(thread_id, _NUM_IMAGES)
    print(f"[IMAGE ASSEMBLY] Computed {len(image_urls)} URLs for thread {thread_id}")

    # Replace IMAGE_N tokens in lesson markdown
    lesson_markdown = state.get("lesson_markdown") or ""
    updated_markdown = _replace_image_tokens(lesson_markdown, image_urls)

    return {
        "image_urls": image_urls,
        "lesson_markdown": updated_markdown,
    }
