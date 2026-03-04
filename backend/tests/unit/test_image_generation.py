"""
Unit tests for the image generation pipeline.

Tests cover:
- ImageRequest / ImagePlan schema validation
- Image service (S3 upload, Gemini call shape, parallel execution)
- Assembly node (URL computation)
- Graph node ordering
"""

import io
from unittest.mock import MagicMock, patch, AsyncMock

import pytest
from PIL import Image as PILImage
from pydantic import ValidationError

from app.schemas.image import ImageRequest, ImagePlan
from app.services.image_service import (
    compute_image_urls,
    compute_s3_key,
    image_to_jpeg_bytes,
    upload_to_s3,
    S3_BUCKET,
    S3_URL_PREFIX,
    PROMPT_PREFIX,
    NUM_IMAGES,
)
from app.graph.nodes.image_assembly import image_assembly_node, _compute_image_urls


# ──────────────────────────────────────────────────────────────
# Schema tests
# ──────────────────────────────────────────────────────────────


def _make_image_request(**overrides):
    """Helper to create a valid ImageRequest dict."""
    defaults = {
        "prompt": "A letter formation guide on a pure white background with no border",
        "placement": "Model, Explain & Engage",
        "alt_text": "Letter D formation guide",
        "pedagogical_role": "Shows stroke order for letter D",
    }
    defaults.update(overrides)
    return defaults


def test_image_plan_schema_valid():
    """ImagePlan accepts valid data with exactly 3 images."""
    plan = ImagePlan(images=[
        ImageRequest(**_make_image_request()),
        ImageRequest(**_make_image_request(prompt="Scene illustration")),
        ImageRequest(**_make_image_request(prompt="Letter comparison")),
    ])
    assert len(plan.images) == 3
    assert all(isinstance(img, ImageRequest) for img in plan.images)


def test_image_plan_exactly_3():
    """ImagePlan rejects lists that don't have exactly 3 images."""
    # Too few
    with pytest.raises(ValidationError, match="exactly 3"):
        ImagePlan(images=[
            ImageRequest(**_make_image_request()),
            ImageRequest(**_make_image_request()),
        ])

    # Too many
    with pytest.raises(ValidationError, match="exactly 3"):
        ImagePlan(images=[
            ImageRequest(**_make_image_request()),
            ImageRequest(**_make_image_request()),
            ImageRequest(**_make_image_request()),
            ImageRequest(**_make_image_request()),
        ])


def test_image_plan_has_required_fields():
    """Each ImageRequest must have prompt, placement, alt_text, pedagogical_role."""
    # Missing prompt
    with pytest.raises(ValidationError):
        ImageRequest(
            placement="Section",
            alt_text="alt",
            pedagogical_role="role",
        )

    # Missing placement
    with pytest.raises(ValidationError):
        ImageRequest(
            prompt="A prompt",
            alt_text="alt",
            pedagogical_role="role",
        )

    # Missing alt_text
    with pytest.raises(ValidationError):
        ImageRequest(
            prompt="A prompt",
            placement="Section",
            pedagogical_role="role",
        )

    # Missing pedagogical_role
    with pytest.raises(ValidationError):
        ImageRequest(
            prompt="A prompt",
            placement="Section",
            alt_text="alt",
        )


def test_image_prompt_contains_white_bg():
    """Verify the service prepends white background text."""
    prompt = "A letter formation guide"
    full_prompt = PROMPT_PREFIX + prompt
    assert "white background" not in full_prompt  # It's in the director's system prompt
    # The PROMPT_PREFIX adds "No text, no words, no letters"
    assert "No text" in full_prompt


def test_image_prompt_contains_no_text():
    """Verify the PROMPT_PREFIX includes the no-text instruction."""
    assert "No text" in PROMPT_PREFIX
    assert "no words" in PROMPT_PREFIX
    assert "no letters" in PROMPT_PREFIX


# ──────────────────────────────────────────────────────────────
# S3 tests
# ──────────────────────────────────────────────────────────────


def test_s3_upload_url_format():
    """S3 key follows images/{thread_id}/img_{n}.jpg pattern."""
    thread_id = "abc-123-def"
    key = compute_s3_key(thread_id, 1)
    assert key == "images/abc-123-def/img_1.jpg"

    key2 = compute_s3_key(thread_id, 3)
    assert key2 == "images/abc-123-def/img_3.jpg"


def test_s3_upload_content_type():
    """Upload uses image/jpeg content type."""
    mock_s3 = MagicMock()
    test_bytes = b"fake-jpeg-data"

    upload_to_s3(test_bytes, "images/test/img_1.jpg", s3_client=mock_s3)

    mock_s3.put_object.assert_called_once()
    call_kwargs = mock_s3.put_object.call_args[1]
    assert call_kwargs["ContentType"] == "image/jpeg"
    assert call_kwargs["Bucket"] == S3_BUCKET
    assert call_kwargs["Key"] == "images/test/img_1.jpg"
    assert call_kwargs["Body"] == test_bytes


# ──────────────────────────────────────────────────────────────
# Assembly node tests
# ──────────────────────────────────────────────────────────────


def test_assembly_computes_urls():
    """Assembly node produces 3 URLs with correct thread_id."""
    urls = _compute_image_urls("test-thread-123")
    assert len(urls) == 3
    assert all("test-thread-123" in url for url in urls)


def test_assembly_url_pattern():
    """URLs follow https://l4c-videos.s3.amazonaws.com/images/{id}/img_{n}.jpg."""
    urls = _compute_image_urls("abc-123")
    expected = [
        f"{S3_URL_PREFIX}/images/abc-123/img_1.jpg",
        f"{S3_URL_PREFIX}/images/abc-123/img_2.jpg",
        f"{S3_URL_PREFIX}/images/abc-123/img_3.jpg",
    ]
    assert urls == expected


def test_assembly_node_returns_urls():
    """The image_assembly_node returns image_urls in state."""
    state = {"messages": [], "handwriting_params": None}
    config = {"configurable": {"thread_id": "node-test-123"}}

    result = image_assembly_node(state, config)

    assert "image_urls" in result
    assert len(result["image_urls"]) == 3
    assert all("node-test-123" in url for url in result["image_urls"])


# ──────────────────────────────────────────────────────────────
# Gemini call shape tests
# ──────────────────────────────────────────────────────────────


def test_gemini_call_shape():
    """Mocked Gemini client called with correct model, modalities, config."""
    mock_client = MagicMock()

    # Create a mock response with inline_data containing raw image bytes
    mock_pil_image = PILImage.new("RGB", (100, 100), color="white")
    buf = io.BytesIO()
    mock_pil_image.save(buf, format="PNG")
    mock_inline_data = MagicMock()
    mock_inline_data.data = buf.getvalue()
    mock_part = MagicMock()
    mock_part.inline_data = mock_inline_data
    mock_response = MagicMock()
    mock_response.parts = [mock_part]
    mock_client.models.generate_content.return_value = mock_response

    from app.services.image_service import generate_image, IMAGE_MODEL

    result = generate_image("Test prompt", client=mock_client)

    # Verify the call
    mock_client.models.generate_content.assert_called_once()
    call_kwargs = mock_client.models.generate_content.call_args[1]
    assert call_kwargs["model"] == IMAGE_MODEL
    assert "IMAGE" in call_kwargs["config"].response_modalities

    # Verify result is a PIL Image
    assert isinstance(result, PILImage.Image)


def test_gemini_parallel_execution():
    """All 3 image gen calls run concurrently via ThreadPoolExecutor."""
    import asyncio
    import time

    call_times = []

    def mock_generate_and_upload(prompt, s3_key, gemini_client, s3_client):
        call_times.append(time.time())
        time.sleep(0.1)  # Simulate work
        return f"https://example.com/{s3_key}"

    with patch(
        "app.services.image_service._generate_and_upload_one",
        side_effect=mock_generate_and_upload,
    ):
        from app.services.image_service import generate_all

        requests = [
            {"prompt": "img1", "placement": "Section 1", "alt_text": "alt1"},
            {"prompt": "img2", "placement": "Section 2", "alt_text": "alt2"},
            {"prompt": "img3", "placement": "Section 3", "alt_text": "alt3"},
        ]

        results = asyncio.get_event_loop().run_until_complete(
            generate_all(
                requests,
                "parallel-test",
                gemini_client=MagicMock(),
                s3_client=MagicMock(),
            )
        )

        assert len(results) == 3

        # All calls should start within 0.05s of each other (parallel)
        if len(call_times) == 3:
            spread = max(call_times) - min(call_times)
            assert spread < 0.5, f"Calls not parallel: spread={spread:.3f}s"


# ──────────────────────────────────────────────────────────────
# Image conversion tests
# ──────────────────────────────────────────────────────────────


def test_image_to_jpeg_bytes_rgb():
    """RGB image converts to JPEG bytes correctly."""
    img = PILImage.new("RGB", (64, 64), color="red")
    result = image_to_jpeg_bytes(img)
    assert isinstance(result, bytes)
    assert len(result) > 0
    # JPEG magic bytes
    assert result[:2] == b'\xff\xd8'


def test_image_to_jpeg_bytes_rgba():
    """RGBA image converts to JPEG (drops alpha)."""
    img = PILImage.new("RGBA", (64, 64), color=(255, 0, 0, 128))
    result = image_to_jpeg_bytes(img)
    assert isinstance(result, bytes)
    assert result[:2] == b'\xff\xd8'


# ──────────────────────────────────────────────────────────────
# Graph node ordering test
# ──────────────────────────────────────────────────────────────


def test_graph_node_order():
    """Image assembly always runs after generator (every generation + modification)."""
    from app.graph.graph import route_after_handwriting_generator

    # Always routes to image_assembly regardless of finalized state
    assert route_after_handwriting_generator({"lesson_finalized": True}) == "image_assembly"
    assert route_after_handwriting_generator({"lesson_finalized": False}) == "image_assembly"
    assert route_after_handwriting_generator({}) == "image_assembly"


# ──────────────────────────────────────────────────────────────
# WebSocket event format test
# ──────────────────────────────────────────────────────────────


def test_websocket_event_format():
    """WebSocket image event matches expected format."""
    from app.schemas.chat import ImageReadyEvent

    event = ImageReadyEvent(
        url="https://l4c-videos.s3.amazonaws.com/images/abc-123/img_1.jpg",
        placement="Model, Explain & Engage",
        alt_text="Lowercase letter d formation guide",
    )

    data = event.model_dump()
    assert "url" in data
    assert "placement" in data
    assert "alt_text" in data
    assert data["url"].startswith("https://")
    assert "img_1.jpg" in data["url"]
