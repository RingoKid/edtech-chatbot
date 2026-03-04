"""
Unit tests for PDF export functionality.

Tests cover:
- PDF endpoint returns correct content type
- HTML building from markdown with embedded images
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.routers.export import _build_html, _extract_lesson_text_from_state


# ──────────────────────────────────────────────────────────────
# HTML building tests
# ──────────────────────────────────────────────────────────────


def test_build_html_basic():
    """_build_html converts markdown to HTML with CSS."""
    lesson_md = "# My Lesson\n\nThis is a paragraph."
    html = _build_html(lesson_md)

    assert "<!DOCTYPE html>" in html
    assert "<style>" in html
    assert "My Lesson" in html
    assert "This is a paragraph" in html


def test_build_html_with_embedded_images():
    """_build_html renders embedded markdown images as <img> tags."""
    lesson_md = (
        "# Lesson Title\n\n"
        "## Section One\n\nContent here.\n\n"
        "![A formation guide](https://l4c-videos.s3.amazonaws.com/images/test/img_1.jpg)\n\n"
        "## Section Two\n\nMore content.\n\n"
        "![Practice worksheet](https://l4c-videos.s3.amazonaws.com/images/test/img_2.jpg)\n"
    )

    html = _build_html(lesson_md)

    assert "img_1.jpg" in html
    assert "img_2.jpg" in html
    assert "<img" in html
    assert "l4c-videos.s3.amazonaws.com" in html


def test_build_html_no_images():
    """HTML renders correctly with no images in markdown."""
    lesson_md = "# Simple Lesson\n\nNo images needed."
    html = _build_html(lesson_md)

    assert "<img" not in html
    assert "Simple Lesson" in html


def test_build_html_img_css_centered():
    """CSS styles images as centered blocks, not floated right."""
    lesson_md = "# Lesson\n\n![desc](https://example.com/img.jpg)"
    html = _build_html(lesson_md)

    assert "display: block" in html
    assert "margin: 12px auto" in html
    assert "max-width: 350px" in html
    # Old floating style should NOT be present
    assert "float: right" not in html


# ──────────────────────────────────────────────────────────────
# Lesson text extraction
# ──────────────────────────────────────────────────────────────


def test_extract_lesson_text_from_state():
    """Reads lesson_markdown directly from state values."""
    state_values = {"lesson_markdown": "# My Lesson\n\nThis is the content."}
    result = _extract_lesson_text_from_state(state_values)
    assert result == "# My Lesson\n\nThis is the content."


def test_extract_lesson_text_from_state_empty():
    """Returns empty string when lesson_markdown not in state."""
    assert _extract_lesson_text_from_state({}) == ""
    assert _extract_lesson_text_from_state({"lesson_markdown": None}) == ""


# ──────────────────────────────────────────────────────────────
# PDF endpoint test (using mocks)
# ──────────────────────────────────────────────────────────────


def test_pdf_endpoint_returns_pdf():
    """Export endpoint returns Content-Type: application/pdf."""
    from app.main import app
    from app.dependencies.auth import get_current_user
    from tests.conftest import get_test_user

    # Override auth dependency
    app.dependency_overrides[get_current_user] = lambda: get_test_user()

    # Mock the ChatService methods
    mock_state = MagicMock()
    mock_state.values = {
        "lesson_markdown": "# My Lesson\n\n" + "Content. " * 100,
    }

    with patch(
        "app.routers.export.ChatService"
    ) as MockChatService:
        instance = MockChatService.return_value
        instance._get_graph = AsyncMock()

        mock_graph = AsyncMock()
        mock_graph.aget_state = AsyncMock(return_value=mock_state)
        instance._get_graph.return_value = mock_graph

        client = TestClient(app)
        response = client.post("/api/v1/chat/test-thread/export-pdf")

    # Clean up overrides
    app.dependency_overrides.clear()

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    # PDF magic bytes
    assert response.content[:4] == b'%PDF'
