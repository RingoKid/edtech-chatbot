"""
Image generation service — Gemini image API + S3 upload.

Generates lesson images using google-genai SDK (Gemini 2.5 Flash Image model)
and uploads them to S3 for embedding in lesson plans.
"""

import io
import os
import logging
from concurrent.futures import ThreadPoolExecutor
import asyncio

import boto3
from google import genai
from google.genai import types
from PIL import Image as PILImage

from app.config import settings

logger = logging.getLogger(__name__)

# Constants
IMAGE_MODEL = "gemini-2.5-flash-image"
S3_BUCKET = "l4c-videos"
S3_URL_PREFIX = f"https://{S3_BUCKET}.s3.amazonaws.com"
PROMPT_PREFIX = "No text, no words, no letters anywhere in the image. "
JPEG_QUALITY = 70
NUM_IMAGES = 3


def get_gemini_client() -> genai.Client:
    """Create a Gemini API client."""
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable is not set")
    return genai.Client(api_key=api_key)


def get_s3_client():
    """Create an S3 client.

    In local dev, dummy AWS_ACCESS_KEY_ID env vars (for DynamoDB Local)
    override ~/.aws/credentials in boto3's chain. We create an explicit
    session from the credentials file to bypass this.
    In production (App Runner), no credentials file exists so we fall
    back to the default chain (IAM role).
    """
    creds_path = os.path.expanduser("~/.aws/credentials")
    if os.path.exists(creds_path):
        session = boto3.Session(profile_name="default")
        return session.client("s3", region_name=settings.aws_region)
    return boto3.client("s3", region_name=settings.aws_region)


def compute_image_urls(thread_id: str, count: int = NUM_IMAGES) -> list[str]:
    """
    Compute pre-known S3 URLs for lesson images.

    These URLs are computed before images exist so the frontend can
    render placeholders while images generate asynchronously.

    Args:
        thread_id: The conversation thread ID
        count: Number of image URLs to generate (default 3)

    Returns:
        List of public S3 URLs
    """
    return [
        f"{S3_URL_PREFIX}/images/{thread_id}/img_{n}.jpg"
        for n in range(1, count + 1)
    ]


def compute_s3_key(thread_id: str, image_index: int) -> str:
    """Compute the S3 object key for an image."""
    return f"images/{thread_id}/img_{image_index}.jpg"


def generate_image(prompt: str, client: genai.Client | None = None) -> PILImage.Image:
    """
    Generate a single image using the Gemini API.

    Args:
        prompt: The image generation prompt
        client: Optional pre-created Gemini client

    Returns:
        PIL Image object
    """
    if client is None:
        client = get_gemini_client()

    full_prompt = PROMPT_PREFIX + prompt

    response = client.models.generate_content(
        model=IMAGE_MODEL,
        contents=full_prompt,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE"],
            image_config=types.ImageConfig(
                aspect_ratio="3:2",
            ),
        ),
    )

    # Extract image from response parts
    # Note: part.as_image() returns google.genai.types.Image (Pydantic model),
    # NOT a PIL Image. We decode the raw bytes from inline_data instead.
    if response.parts:
        for part in response.parts:
            if part.inline_data is not None and part.inline_data.data:
                return PILImage.open(io.BytesIO(part.inline_data.data))

    raise RuntimeError("Gemini API did not return an image")


def image_to_jpeg_bytes(image: PILImage.Image) -> bytes:
    """Convert a PIL Image to JPEG bytes."""
    buffer = io.BytesIO()
    # Convert RGBA to RGB if needed (JPEG doesn't support alpha)
    if image.mode in ("RGBA", "LA", "P"):
        image = image.convert("RGB")
    image.save(buffer, format="JPEG", quality=JPEG_QUALITY)
    buffer.seek(0)
    return buffer.read()


def upload_to_s3(
    image_bytes: bytes,
    s3_key: str,
    s3_client=None,
) -> str:
    """
    Upload JPEG bytes to S3.

    Args:
        image_bytes: JPEG image data
        s3_key: The S3 object key
        s3_client: Optional pre-created S3 client

    Returns:
        The public URL of the uploaded image
    """
    if s3_client is None:
        s3_client = get_s3_client()

    s3_client.put_object(
        Bucket=S3_BUCKET,
        Key=s3_key,
        Body=image_bytes,
        ContentType="image/jpeg",
        CacheControl="max-age=31536000",
    )

    return f"{S3_URL_PREFIX}/{s3_key}"


def _generate_and_upload_one(
    prompt: str,
    s3_key: str,
    gemini_client: genai.Client,
    s3_client,
) -> str:
    """
    Generate one image and upload it to S3 (synchronous, for thread pool).

    Returns the public S3 URL.
    """
    logger.info(f"Generating image for key: {s3_key}")
    image = generate_image(prompt, client=gemini_client)
    jpeg_bytes = image_to_jpeg_bytes(image)
    url = upload_to_s3(jpeg_bytes, s3_key, s3_client=s3_client)
    logger.info(f"Uploaded image to: {url}")
    return url


async def generate_all(
    image_requests: list[dict],
    thread_id: str,
    gemini_client: genai.Client | None = None,
    s3_client=None,
) -> list[dict]:
    """
    Generate all lesson images in parallel and upload to S3.

    Uses a ThreadPoolExecutor because the google-genai SDK is sync-only.

    Args:
        image_requests: List of ImageRequest dicts with 'prompt' key
        thread_id: The conversation thread ID
        gemini_client: Optional pre-created Gemini client
        s3_client: Optional pre-created S3 client

    Returns:
        List of dicts with {url, alt_text} for each image
    """
    if gemini_client is None:
        gemini_client = get_gemini_client()
    if s3_client is None:
        s3_client = get_s3_client()

    loop = asyncio.get_running_loop()
    results = []

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = []
        for i, req in enumerate(image_requests):
            s3_key = compute_s3_key(thread_id, i + 1)
            future = loop.run_in_executor(
                executor,
                _generate_and_upload_one,
                req["prompt"],
                s3_key,
                gemini_client,
                s3_client,
            )
            futures.append((future, req))

        for future, req in futures:
            url = await future
            results.append({
                "url": url,
                "alt_text": req.get("alt_text", ""),
            })

    return results
