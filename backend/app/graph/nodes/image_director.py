"""
Image director node — LLM-powered image planning + generation orchestration.

1. Reads the completed lesson markdown + handwriting params from state
2. Calls LLM (gpt-4o) with structured output → ImagePlan (3 images)
3. Generates 3 images in parallel via Gemini API
4. Uploads to pre-known S3 URLs
5. Sends WebSocket events per image (if websocket is available)
"""

import logging

from langchain_core.runnables import RunnableConfig

from app.graph.state import GraphState
from app.llm.client import get_chat_model
from app.schemas.image import ImagePlan

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
if not logger.handlers:
    logger.addHandler(logging.StreamHandler())

DIRECTOR_MODEL = "gpt-4o"

IMAGE_DIRECTOR_SYSTEM_PROMPT = """\
You are an educational image director for early childhood
literacy lesson plans (Pre-K through 2nd grade).

Your job: read a completed lesson plan and create exactly
3 image generation prompts that directly support the
lesson's activities. These images will be printed on
white paper and used in real classrooms.

═══════════════════════════════════════════════════
EDUCATIONAL DESIGN PRINCIPLES
═══════════════════════════════════════════════════

An image is FUNCTIONAL if removing it would break the
activity. An image is DECORATIVE if a stock photo could
replace it. Only create functional images.

Functional image examples:
- A letter formation guide with stroke order, numbered
  steps, starting dot, and directional arrows on writing
  lines — this IS the instruction
- A scene illustration for a decodable text where every
  object starts with the target sound — this IS the
  phonemic awareness exercise
- A side-by-side comparison of commonly confused letters
  (b/d, p/q) with color-coded differences — this IS the
  visual discrimination task

Ask yourself for each image:
1. Does the student interact WITH this image?
2. Does an activity in the lesson DEPEND on this image?
3. Would the teacher have to CREATE this image by hand
   if we didn't provide it?

If the answer to any of these is "no" — don't make it.

Age-appropriate means:
- Simple, rounded, friendly shapes (no sharp/angular art)
- Bright but not neon colors
- Maximum 3-4 objects per scene (young children get
  overwhelmed by visual clutter)
- Characters should be diverse and welcoming
- No text or letters inside illustrations (the lesson
  provides the text separately)

═══════════════════════════════════════════════════
IMAGE GENERATION PROMPT RULES
═══════════════════════════════════════════════════

Every prompt you write MUST include:
- "on a pure white background with no border"
- "designed for printing on standard white paper"
- The specific art style: "clean, simple, rounded
  children's book illustration style"
- Explicit description of EVERY object (don't assume
  the model will infer educational intent)

For letter formation guides specifically:
- Always include: "with light gray horizontal writing
  lines (top line, dashed midline, solid baseline)"
- Specify stroke order with numbered steps
- Include "a small green dot at the starting point"
- Specify direction with arrows and words like
  "counterclockwise" or "top to bottom"
- Name the exact letter, case, and font style

For scene illustrations:
- Name every object that should appear
- Specify spatial relationships ("a dog NEXT TO a door")
- Limit to 3-4 objects maximum
- State what should NOT be in the image

For confused letter pairs:
- Show both letters side by side, same size
- Use color coding (e.g., red highlight on the
  distinguishing feature)
- Include directional indicators showing the difference

═══════════════════════════════════════════════════
PLACEMENT RULES
═══════════════════════════════════════════════════

Place images where they're needed in the lesson flow:
- Formation guides → in "Model, Explain & Engage" section
- Scene illustrations → in "Application" section
- Comparison/discrimination → in "Review & Connect" section

Each image must specify its placement as the exact
section header string it should appear after.

═══════════════════════════════════════════════════
OUTPUT
═══════════════════════════════════════════════════

Return exactly 3 images. For each provide:
- prompt: Full image generation prompt (be verbose and
  explicit — the image model has no educational context)
- placement: Section header string to place image after
- alt_text: Accessible description for screen readers
- pedagogical_role: One sentence on why this image exists\
"""

USER_MESSAGE_TEMPLATE = """\
Here is the lesson plan to illustrate:

Grade: {grade}
Letter: {letter}
Student Level: {student_level}

---

{lesson_markdown}"""


def _extract_lesson_markdown(state: GraphState) -> str:
    """Read lesson markdown from state (set by handwriting_generator_node)."""
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
    Image director: plan images with LLM, then kick off generation in background.

    This node:
    1. Reads lesson content + params from state
    2. Calls gpt-4o with structured output → ImagePlan
    3. Kicks off Gemini image generation as a background task (non-blocking)
    4. Returns image_requests to state immediately

    The lesson text + feedback flow is NOT blocked by image generation.
    Images upload to pre-known S3 URLs asynchronously (~10-15s after response).
    """
    thread_id = config.get("configurable", {}).get("thread_id", "unknown")

    # Extract lesson content and params
    lesson_markdown = _extract_lesson_markdown(state)
    params = state.get("handwriting_params", {})

    if not lesson_markdown:
        logger.warning("No lesson markdown found in state — skipping image generation")
        return {"image_requests": None}

    grade = params.get("grade", "K")
    letter = params.get("letter", "A")
    student_level = params.get("student_level", "on-level")

    # Step 1: Call LLM to plan images (this is fast, ~2-3s)
    logger.info(f"Image director: planning images for thread {thread_id}")
    model = get_chat_model(DIRECTOR_MODEL)
    structured_model = model.with_structured_output(ImagePlan)

    user_message = USER_MESSAGE_TEMPLATE.format(
        grade=grade,
        letter=letter,
        student_level=student_level,
        lesson_markdown=lesson_markdown,
    )

    try:
        image_plan: ImagePlan = await structured_model.ainvoke([
            {"role": "system", "content": IMAGE_DIRECTOR_SYSTEM_PROMPT},
            {"role": "user", "content": user_message},
        ])
    except Exception as e:
        logger.error(f"Image planning failed: {e}")
        return {"image_requests": None}

    # Serialize to dicts for state storage
    image_requests = [img.model_dump() for img in image_plan.images]

    # Step 2: Fire-and-forget background task for Gemini generation + S3 upload
    # This returns immediately — images appear at pre-known URLs ~10-15s later
    import asyncio
    asyncio.create_task(_background_generate_images(image_requests, thread_id))

    return {
        "image_requests": image_requests,
    }
