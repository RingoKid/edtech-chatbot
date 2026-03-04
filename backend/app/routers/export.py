"""
PDF export router — generates downloadable PDF lesson plans with embedded images.

Uses WeasyPrint for server-side HTML→PDF rendering with print-optimized CSS.
"""

import logging
from io import BytesIO

import markdown
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from weasyprint import HTML

from app.services.chat_service import ChatService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["export"])

PRINT_CSS = """\
@page {
    size: letter;
    margin: 0.75in;
    @bottom-center {
        content: counter(page);
        font-size: 10px;
        color: #888;
    }
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto,
                 "Noto Color Emoji", "Apple Color Emoji", "Segoe UI Emoji", sans-serif;
    font-size: 12px;
    line-height: 1.5;
    color: #1a1a1a;
    max-width: 100%;
}

h1 {
    font-size: 18px;
    margin-top: 16px;
    margin-bottom: 8px;
    color: #2d3748;
    border-bottom: 2px solid #e2e8f0;
    padding-bottom: 4px;
}

h2 {
    font-size: 15px;
    margin-top: 14px;
    margin-bottom: 6px;
    color: #2d3748;
    border-bottom: 1px solid #e2e8f0;
    padding-bottom: 3px;
}

h3 {
    font-size: 13px;
    margin-top: 10px;
    margin-bottom: 4px;
    color: #4a5568;
}

p { margin-bottom: 6px; }

ul, ol {
    margin-bottom: 8px;
    padding-left: 20px;
}

li { margin-bottom: 3px; }

img {
    display: block;
    max-width: 350px;
    margin: 12px auto;
    border-radius: 4px;
    border: 1px solid #e2e8f0;
}

table {
    width: 100%;
    border-collapse: collapse;
    margin: 8px 0;
    font-size: 11px;
}

th, td {
    border: 1px solid #cbd5e0;
    padding: 4px 8px;
    text-align: left;
}

th { background: #edf2f7; font-weight: 600; }

blockquote {
    border-left: 3px solid #cbd5e0;
    padding-left: 10px;
    color: #4a5568;
    font-style: italic;
    margin: 8px 0;
}

hr {
    border: none;
    border-top: 1px solid #e2e8f0;
    margin: 12px 0;
}

/* Prevent page breaks mid-section */
h1, h2, h3 { break-after: avoid; }
section, .section { break-inside: avoid; }
"""


def _extract_lesson_text_from_state(state_values: dict) -> str:
    """Read lesson markdown directly from graph state."""
    return state_values.get("lesson_markdown") or ""


def _build_html(lesson_md: str) -> str:
    """Convert lesson markdown to full HTML document with print CSS.

    Images are already embedded in the markdown as ![alt](url) syntax,
    which the markdown parser converts to <img> tags automatically.
    """
    html_body = markdown.markdown(
        lesson_md,
        extensions=["tables", "fenced_code"],
    )

    return f"""\
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <style>{PRINT_CSS}</style>
</head>
<body>
{html_body}
</body>
</html>"""


@router.post("/{thread_id}/export-pdf")
async def export_pdf(thread_id: str):
    """
    Generate and download a PDF of the lesson plan for a given thread.

    1. Fetches conversation messages from checkpoint state
    2. Extracts the lesson markdown (with embedded image URLs)
    3. Renders HTML with print-optimized CSS
    4. Converts to PDF via WeasyPrint
    """
    chat_service = ChatService()

    # Read lesson content directly from graph state
    graph = await chat_service._get_graph()
    config = {"configurable": {"thread_id": thread_id}}
    state = await graph.aget_state(config)

    if not state or not state.values:
        raise HTTPException(status_code=404, detail="Thread not found")

    lesson_md = _extract_lesson_text_from_state(state.values)
    if not lesson_md:
        raise HTTPException(
            status_code=404,
            detail="No lesson content found in this thread",
        )

    # Build HTML and convert to PDF
    html_str = _build_html(lesson_md)

    try:
        pdf_bytes = HTML(string=html_str).write_pdf()
    except Exception as e:
        logger.error(f"PDF generation failed: {e}")
        raise HTTPException(status_code=500, detail="Failed to generate PDF")

    # Return as downloadable file
    return StreamingResponse(
        BytesIO(pdf_bytes),
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="lesson-{thread_id[:8]}.pdf"',
        },
    )
