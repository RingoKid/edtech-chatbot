# 021: Lesson Image Generation

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| `ImageRequest` schema | ✅ Done | `app/schemas/image.py` — `prompt` + `alt_text` only |
| GraphState fields | ✅ Done | `app/graph/state.py` — `image_requests`, `image_urls`, `lesson_markdown` |
| Generator image placeholders | ✅ Done | Rule 19 in generator prompt — places `![desc](IMAGE_N)` inline |
| Assembly node | ✅ Done | `app/graph/nodes/image_assembly.py` — computes URLs + replaces IMAGE_N tokens |
| Image director node | ✅ Done | `app/graph/nodes/image_director.py` — regex extraction + STYLE_SUFFIX, no LLM call |
| Image generation service | ✅ Done | `app/services/image_service.py` — Gemini 2.5 Flash via `google-genai` SDK |
| S3 upload service | ✅ Done | `app/services/image_service.py` — parallel upload via ThreadPoolExecutor |
| Graph wiring | ✅ Done | `app/graph/graph.py` — generator → assembly → director → END |
| `lesson_markdown` in state | ✅ Done | Set by `handwriting_generator_node`, tokens replaced by assembly |
| Frontend: image rendering | ✅ Done | `MarkdownRenderer.jsx` — `LessonImage` component with skeleton + auto-retry |
| Frontend: export button | ✅ Done | `Chatbot2.jsx` — detects S3 URLs in reply text |
| PDF export endpoint | ✅ Done | `app/routers/export.py` — reads `state.lesson_markdown`, centered images, emoji font |
| Unit tests | ✅ Done | 24 tests (17 image + 7 PDF), all passing |

## Overview

**Status:** Implemented (v2)
**Layer:** Post-generation (runs after handwriting generator)
**Image Model:** `gemini-2.5-flash-image` via `google-genai` SDK (v1.65.0)
**Framework:** LangGraph nodes (no LLM calls in image pipeline)

The handwriting generator places exactly 3 image placeholders (`![description](IMAGE_N)`) directly in the lesson markdown while writing. The assembly node replaces tokens with pre-known S3 URLs. The image director extracts descriptions via regex, prepends a style suffix, and fires off Gemini generation as a background task. Images appear at pre-known S3 URLs ~10-15s after the response.

A companion PDF export feature reads `state.lesson_markdown` directly and renders via `weasyprint` with emoji font support. Images are already embedded in the markdown, so the markdown parser handles `<img>` rendering natively.

---

## Architecture Context

```
                FROM HANDWRITING GENERATOR
                (lesson markdown with ![desc](IMAGE_N) placeholders)
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│              Assembly Node (pure function)                │
│                                                          │
│  1. Compute pre-known S3 URLs using thread_id            │
│     s3://l4c-videos/images/{thread_id}/img_{n}.jpg       │
│  2. Replace IMAGE_N tokens in lesson_markdown with URLs  │
│  3. Store URLs in state.image_urls                       │
│  4. Store updated markdown in state.lesson_markdown      │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│              Image Director (no LLM call)                │
│                                                          │
│  1. Regex-extract descriptions from                      │
│     ![desc](https://l4c-videos...) patterns              │
│  2. Prepend STYLE_SUFFIX to each → Gemini prompt         │
│  3. Fire-and-forget: asyncio.create_task() for           │
│     parallel Gemini generation + S3 upload               │
│  4. Return image_requests to state immediately           │
└──────────────────────────────────────────────────────────┘
```

### End-to-End Flow

```
1. Generator produces lesson markdown with ![desc](IMAGE_N) placeholders
2. Assembly node computes S3 URLs, replaces tokens in lesson_markdown
3. Image director extracts descriptions via regex, kicks off Gemini (background)
4. Graph ends → ChatService replaces any remaining IMAGE_N tokens in reply
5. Frontend renders markdown with <img> tags (LessonImage component)
6. Images show skeleton placeholder, auto-retry every 3s until Gemini uploads complete
7. ~10-15s later: images appear at pre-known S3 URLs
```

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Generator-driven placement | Generator places `![desc](IMAGE_N)` | Generator knows lesson structure — no separate LLM call needed |
| No gpt-4o director | Regex extraction + style suffix | Eliminates ~$0.03/lesson, ~10-15s latency, ~150 lines of code |
| Image count | Fixed at 3 | Enough for pedagogical value, not so many it slows delivery |
| Pre-known URLs | `images/{thread_id}/img_{n}.jpg` | Decouples text delivery from image generation |
| Frontend retry | Skeleton + 3s polling with cache-busting | No WebSocket needed — simple, robust |
| Image model | `gemini-2.5-flash-image` | Already proven in existing image generation workflow |
| PDF rendering | Backend `weasyprint` | Consistent print layout, independent of browser |
| S3 bucket | `l4c-videos` (existing) | Reuse existing bucket, add `images/` prefix |
| Image delivery | HTTP response (ADR-001) | Simpler than WebSocket events, images in markdown |

---

## Schemas

### ImageRequest

```
ImageRequest:
    prompt: str     — Full image generation prompt (description + style suffix)
    alt_text: str   — Accessible description for screen readers
```

### GraphState Fields

| Field | Type | Purpose |
|-------|------|---------|
| `lesson_markdown` | `Optional[str]` | Lesson content — set by generator, tokens replaced by assembly |
| `image_requests` | `Optional[list[dict]]` | `{prompt, alt_text}` dicts extracted by image director |
| `image_urls` | `Optional[list[str]]` | Pre-computed S3 URLs for the 3 images |

---

## Generator Image Placeholder Rule

Rule 19 in the handwriting generator prompt instructs the LLM to place exactly 3 image placeholders:

```
19. **Image Placeholders**: Place EXACTLY 3 image placeholders using:
   ![2-3 sentence description](IMAGE_N) where N is 1, 2, or 3.
   - IMAGE_1 → in Section 2 (Model, Explain & Engage)
   - IMAGE_2 → in Section 3 (Guided Practice)
   - IMAGE_3 → in Section 4 (Application)
   Description focuses on pedagogical content only (no style boilerplate).
```

---

## Image Director — Style Suffix

The director prepends this to each description before sending to Gemini:

```
STYLE_SUFFIX = " Clean, simple, rounded children's book illustration style.
On a pure white background with no border, designed for printing on standard
white paper. Age-appropriate for early childhood (PreK-1st grade). Bright but
not neon colors, simple rounded shapes, maximum 3-4 objects."
```

---

## Image Generation Service

### API Integration

Uses the `google-genai` Python SDK.

**Environment variable:** `GEMINI_API_KEY`
**Model:** `gemini-2.5-flash-image`

**Call pattern:**
1. Create `genai.Client(api_key=...)`
2. Call `client.models.generate_content()` with `response_modalities=["IMAGE"]`
3. Extract `inline_data` from response parts
4. Save as PIL Image → convert to JPEG (quality=70)
5. Upload JPEG bytes to S3

**Image config:**
- Aspect ratio: `3:2` (landscape, better for lesson embedding)
- Prompt prefix: `"No text, no words, no letters anywhere in the image. "`

### Parallel Generation

All 3 images generated concurrently using `ThreadPoolExecutor(max_workers=3)`. Expected wall time: 10-15 seconds for all 3.

---

## S3 Storage

### Bucket & Path Convention

| Item | Value |
|------|-------|
| Bucket | `l4c-videos` |
| Path pattern | `images/{thread_id}/img_{n}.jpg` |
| Public URL | `https://l4c-videos.s3.amazonaws.com/images/{thread_id}/img_1.jpg` |

### Upload Configuration

- Content type: `image/jpeg`
- Cache-Control: `max-age=31536000` (immutable — thread_id makes each path unique)

---

## Graph Changes

### Flow (Handwriting Path Only)

```
routing_agent → param_agent → handwriting_generator → image_assembly → image_director → END
```

Images generate on **every** generator invocation (initial generation AND modifications).

### Node Definitions

**handwriting_generator** — ReAct agent (existing)
- Generates lesson with `![desc](IMAGE_N)` placeholders (Rule 19)
- Saves last AI message content to `state.lesson_markdown`

**image_assembly** — Pure function (no LLM)
- Computes 3 pre-known S3 URLs from `thread_id`
- Replaces `IMAGE_N` tokens in `lesson_markdown` with URLs
- Writes `image_urls` + updated `lesson_markdown` to state

**image_director** — Regex + background task (no LLM)
- Extracts `![desc](https://l4c-videos...)` patterns via regex
- Prepends `STYLE_SUFFIX` to each description → Gemini prompt
- Kicks off Gemini generation as `asyncio.create_task()` (fire-and-forget)
- Returns `image_requests` to state immediately

---

## PDF Export

### Endpoint

```
POST /api/v1/chat/{thread_id}/export-pdf
```

**Response:** PDF file download (Content-Type: `application/pdf`)

### How It Works

1. Reads `state.lesson_markdown` from graph state (images already embedded as `![alt](url)`)
2. Converts markdown → HTML via `markdown` library (native `<img>` rendering)
3. Applies print CSS (images centered at `max-width: 350px`)
4. Converts HTML → PDF via `weasyprint`

---

## Frontend

### MarkdownRenderer.jsx — `LessonImage` Component

Standalone React component for each image with:
- **Skeleton placeholder** — pulsing gray box with image icon while loading
- **Auto-retry** — on error, retries every 3s with cache-busting (`?t=timestamp`)
- **Max retries** — gives up after 60s (20 retries)
- **Clean transition** — skeleton disappears, image appears on successful load

### Export Button (Chatbot2.jsx)

- Detects images by checking for `l4c-videos.s3.amazonaws.com` in the reply text
- Shows centered "Export Lesson as PDF" button below the lesson

---

## Evaluation (Unit Tests)

### Test Categories

| Test | What It Verifies |
|------|------------------|
| `test_image_request_valid` | `ImageRequest` Pydantic model accepts valid data |
| `test_image_prompt_contains_no_text` | PROMPT_PREFIX includes "no text, no words, no letters" |
| `test_s3_upload_url_format` | S3 key matches `images/{thread_id}/img_{n}.jpg` pattern |
| `test_s3_upload_content_type` | Upload uses `image/jpeg` content type |
| `test_assembly_computes_urls` | Assembly produces 3 URLs with correct thread_id |
| `test_assembly_url_pattern` | URLs follow expected S3 pattern |
| `test_assembly_node_returns_urls` | Node returns `image_urls` in state |
| `test_assembly_replaces_tokens` | Assembly replaces IMAGE_N tokens in lesson_markdown |
| `test_replace_image_tokens` | `_replace_image_tokens()` substitutes all tokens |
| `test_extract_image_descriptions` | Extracts descriptions from markdown with S3 links |
| `test_extract_image_descriptions_no_images` | Returns empty list with no images |
| `test_extract_image_descriptions_ignores_non_s3` | Only extracts l4c-videos URLs |
| `test_gemini_call_shape` | Gemini client called with correct model + config |
| `test_gemini_parallel_execution` | All 3 calls run concurrently |
| `test_image_to_jpeg_bytes_rgb` | RGB → JPEG conversion |
| `test_image_to_jpeg_bytes_rgba` | RGBA → JPEG conversion (drops alpha) |
| `test_graph_node_order` | Assembly always runs after generator |
| `test_build_html_basic` | Markdown → HTML with CSS |
| `test_build_html_with_embedded_images` | Embedded images render as `<img>` tags |
| `test_build_html_no_images` | No images renders correctly |
| `test_build_html_img_css_centered` | CSS uses `display: block; margin: auto`, not `float: right` |
| `test_extract_lesson_text_from_state` | Reads `lesson_markdown` from state |
| `test_extract_lesson_text_from_state_empty` | Returns empty string when absent |
| `test_pdf_endpoint_returns_pdf` | Export endpoint returns `application/pdf` |

### Running Tests

```bash
docker compose exec backend pytest tests/unit/test_image_generation.py tests/unit/test_pdf_export.py -v
```

---

## Implementation Files

### Files

| File | Purpose |
|------|---------|
| `app/graph/agents/handwriting_generator.py` | Rule 19: image placeholder instructions in generator prompt |
| `app/graph/nodes/image_assembly.py` | Computes S3 URLs + replaces IMAGE_N tokens in lesson_markdown |
| `app/graph/nodes/image_director.py` | Regex extraction of descriptions, STYLE_SUFFIX, fire-and-forget Gemini |
| `app/schemas/image.py` | `ImageRequest` Pydantic model (`prompt` + `alt_text`) |
| `app/schemas/chat.py` | `ChatMessageRequest`, `ChatMessageResponse` (no image fields) |
| `app/services/image_service.py` | Gemini image generation + S3 upload service |
| `app/services/chat_service.py` | Simple IMAGE_N → URL replacement in reply text |
| `app/routers/export.py` | PDF export with native markdown image rendering |
| `app/graph/state.py` | `lesson_markdown`, `image_requests`, `image_urls` fields |
| `app/graph/graph.py` | Generator → assembly → director → END wiring |
| `frontend/src/components/MarkdownRenderer.jsx` | `LessonImage` component with skeleton + retry |
| `frontend/src/components/Chatbot2.jsx` | Export button, S3 URL detection |
| `tests/unit/test_image_generation.py` | 17 unit tests for schemas, S3, assembly, director, Gemini |
| `tests/unit/test_pdf_export.py` | 7 unit tests for HTML building, text extraction, PDF endpoint |

---

## Implementation Notes

- `google-genai` SDK v1.65.0: `part.as_image()` returns a Pydantic `Image` model, NOT PIL Image. Use `PILImage.open(io.BytesIO(part.inline_data.data))` instead.
- `response.parts` can be `None` when Gemini refuses a prompt — always guard with `if response.parts:`
- S3 credentials in local dev: Docker container has dummy AWS keys for DynamoDB Local. `get_s3_client()` uses `boto3.Session(profile_name="default")` when `~/.aws/credentials` exists, falling back to default chain (IAM role) in production.
- S3 bucket `l4c-videos` has a bucket policy granting public read — no per-object ACL needed.
- `PROMPT_PREFIX = "No text, no words, no letters anywhere in the image. "` — conflicts with letter comparison prompts. Gemini sometimes refuses these.
- Gemini generation runs as `asyncio.create_task()` (fire-and-forget) so the HTTP response returns immediately.
- `weasyprint` requires system-level libraries + `fonts-noto-color-emoji` for emoji rendering in PDFs.

---

## Bugs Found During Implementation

| Bug | Root Cause | Fix |
|-----|-----------|-----|
| `'Image' object has no attribute 'mode'` | `part.as_image()` returns google-genai Pydantic model, not PIL | Decode raw bytes: `PILImage.open(io.BytesIO(part.inline_data.data))` |
| `'NoneType' object is not iterable` | `response.parts` is `None` when Gemini refuses | Added `if response.parts:` guard |
| S3 `InvalidAccessKeyId` | Dummy env vars override `~/.aws/credentials` in boto3 chain | `get_s3_client()` creates explicit `Session(profile_name="default")` |
| Not all images in PDF | v1: `_build_html()` h2 matching fragile | Fixed in v2: images embedded in markdown, parser handles natively |
| Emojis missing in PDF | Container lacks emoji fonts | Added `fonts-noto-color-emoji` to Dockerfile |
| Export button missing after v2 | Removed `images` array from response | Changed detection to check for S3 URLs in reply text |

---

## Open Questions

1. Should image generation be gated behind a feature flag so it can be disabled in production until proven stable?
2. Should we add Langfuse tracing to the image pipeline for cost/latency monitoring?
3. For non-handwriting lesson types (vocabulary, idea generation) — should images also generate?

---

## Verification

```bash
# Rebuild
docker compose down && docker compose up -d --build
docker compose exec backend python scripts/init_db.py

# Unit tests
docker compose exec backend pytest tests/unit/test_image_generation.py tests/unit/test_pdf_export.py -v

# All unit tests (regression check)
docker compose exec backend pytest tests/unit/ -v

# Health check
curl -s http://localhost:8000/api/v1/health
```

### Done When

- [x] All 24 unit tests pass
- [x] Generator places 3 `![desc](IMAGE_N)` placeholders in lesson markdown
- [x] Assembly replaces tokens with S3 URLs
- [x] Director extracts descriptions and fires off Gemini (no gpt-4o)
- [x] Frontend shows skeleton placeholder, images load via retry
- [x] PDF export renders images centered (not floated)
- [x] Export button appears when lesson has images

---

## Spec Revisions

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-03-03 | Initial draft |
| 1.0 | 2026-03-03 | v1 implementation complete — 22 tests passing. Changed from WebSocket events to image data in HTTP response (ADR-001). |
| 1.1 | 2026-03-04 | Fixed PIL/Pydantic Image bug, S3 credential handling, null safety. Added `lesson_markdown` to state. Simplified routing. Added emoji font to Dockerfile. Documented v2 redesign plan. |
| 2.0 | 2026-03-04 | v2 redesign implemented — generator-driven image placement. Eliminated gpt-4o director call (~$0.03/lesson, ~10-15s). Removed `ImagePlan`, `ImageReadyEvent`, `_inject_images_into_markdown()`. Added `LessonImage` component with skeleton + auto-retry. 24 tests passing (-145 net lines). |
