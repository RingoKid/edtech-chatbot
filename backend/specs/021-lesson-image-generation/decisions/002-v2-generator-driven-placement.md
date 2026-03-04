# ADR-002: v2 Generator-Driven Image Placement

**Date:** 2026-03-04
**Status:** Implemented
**Supersedes:** v1 gpt-4o image director approach

## Context

The v1 image pipeline used a separate gpt-4o call (~$0.03, ~10-15s) to plan what 3 images to generate and where they go in the lesson. This was expensive, slow, and fragile:

- **Cost:** ~$0.03 per lesson for the gpt-4o structured output call
- **Latency:** ~10-15s added to the response pipeline
- **Fragility:** Section header string matching (`_inject_images_into_markdown()`) failed often — placement strings from gpt-4o didn't always match the actual markdown headers
- **Redundancy:** The generator already knows the lesson structure — a second LLM re-reading the same content to decide image placement was unnecessary

## Decision

Move image placement responsibility to the generator itself. The generator places `![description](IMAGE_N)` placeholders directly in the lesson markdown while writing. Downstream nodes handle token replacement and style injection — no LLM calls needed.

## What Changed

### Removed (~150 lines)

| Component | File | What Was Removed |
|-----------|------|-----------------|
| `IMAGE_DIRECTOR_SYSTEM_PROMPT` | `image_director.py` | 120-line gpt-4o system prompt |
| `USER_MESSAGE_TEMPLATE` | `image_director.py` | Template for gpt-4o user message |
| gpt-4o structured output call | `image_director.py` | `model.with_structured_output(ImagePlan).ainvoke()` |
| `ImagePlan` schema | `image.py` | Pydantic model with exactly-3 validator |
| `placement` field | `ImageRequest` | No longer needed — placement is in the markdown |
| `pedagogical_role` field | `ImageRequest` | Was only for traceability, never consumed |
| `ImageReadyEvent` | `chat.py` | No longer sent in response |
| `images` field | `ChatMessageResponse` | Images are in the markdown itself |
| `_inject_images_into_markdown()` | `chat_service.py` | 50-line function for header matching |
| h2-matching image injection | `export.py` | `_build_html()` no longer injects images manually |
| `image_urls` param | `_build_html()` | Markdown parser handles images natively |
| `S3_URL_PREFIX` import | `export.py` | No longer needed |

### Added (~50 lines)

| Component | File | What Was Added |
|-----------|------|---------------|
| Rule 19 | `handwriting_generator.py` | Instructs generator to place 3 `![desc](IMAGE_N)` placeholders |
| `_replace_image_tokens()` | `image_assembly.py` | Replaces `IMAGE_N` → S3 URLs in lesson_markdown |
| `STYLE_SUFFIX` | `image_director.py` | Style boilerplate appended to each description for Gemini |
| `_extract_image_descriptions()` | `image_director.py` | Regex to parse `![desc](https://l4c-videos...)` patterns |
| Simple token replacement | `chat_service.py` | 4-line `IMAGE_N` → URL replacement on reply |
| `LessonImage` component | `MarkdownRenderer.jsx` | Skeleton placeholder + auto-retry for async images |
| S3 URL detection | `Chatbot2.jsx` | Export button triggered by S3 URLs in reply |

### Modified

| Component | File | Change |
|-----------|------|--------|
| `image_assembly_node` | `image_assembly.py` | Now also replaces tokens in `lesson_markdown` (was URL-only) |
| `image_director_node` | `image_director.py` | Regex extraction instead of gpt-4o call |
| `generate_all()` | `image_service.py` | Returns `{url, alt_text}` instead of `{url, placement, alt_text}` |
| `_build_html()` | `export.py` | No `image_urls` param — markdown parser renders `![alt](url)` natively |
| CSS `img` | `export.py` | `display: block; max-width: 350px; margin: 12px auto` (was `float: right; max-width: 200px`) |

## What Stayed Unchanged

- Graph wiring: `generator → image_assembly → image_director → END`
- GraphState fields: `image_requests`, `image_urls`, `lesson_markdown`
- `image_service.py` core: Gemini generation + S3 upload logic
- Assembly node URL computation logic
- Fire-and-forget background generation via `asyncio.create_task()`

## Net Effect

- **Eliminates:** ~$0.03/lesson, ~10-15s latency, ~150 lines of fragile code
- **Adds:** ~50 lines of simpler code (prompt rule + regex + token replacement)
- **Tests:** 24 passing (was 22) — added assembly token replacement + director extraction tests

## Alternatives Considered

1. **Keep gpt-4o but fix header matching** — Doesn't address cost/latency. Header matching is inherently fragile.
2. **Use a cheaper model (gpt-4o-mini) for planning** — Still an unnecessary LLM call when the generator already has the context.
3. **Template-based placement (always sections 2/3/4)** — Too rigid. The generator can make contextual decisions about placement.
