# 021: Lesson Image Generation

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| `ImageRequest` / `ImagePlan` schemas | ✅ Done | `app/schemas/image.py` — will be simplified in v2 |
| GraphState update | ✅ Done | `app/graph/state.py` — `image_requests`, `image_urls`, `lesson_markdown` |
| Image director node | ✅ Done | `app/graph/nodes/image_director.py` — gpt-4o structured output + fire-and-forget Gemini |
| Image generation service | ✅ Done | `app/services/image_service.py` — Gemini 2.5 Flash via `google-genai` SDK |
| S3 upload service | ✅ Done | `app/services/image_service.py` — parallel upload via ThreadPoolExecutor |
| Assembly node | ✅ Done | `app/graph/nodes/image_assembly.py` — computes pre-known URLs |
| Graph wiring | ✅ Done | `app/graph/graph.py` — generator → assembly → director → END (feedback bypassed) |
| Image injection in response | ✅ Done | `app/services/chat_service.py` — `_inject_images_into_markdown()` |
| `lesson_markdown` in state | ✅ Done | Set by `handwriting_generator_node`, read by director + PDF export |
| Frontend: image rendering | ✅ Done | `MarkdownRenderer.jsx` — image styling + lazy loading |
| PDF export endpoint | ✅ Done | `app/routers/export.py` — reads `state.lesson_markdown`, emoji font support |
| Frontend: export button | ✅ Done | `Chatbot2.jsx` — centered "Export Lesson as PDF" button |
| Unit tests | ✅ Done | 22 tests (16 image + 6 PDF), all passing |
| Generator-driven image placement | 🔲 Planned | v2: generator places `![desc](IMAGE_N)` placeholders, eliminates gpt-4o director call |

## Overview

**Status:** Implemented (v1), v2 redesign planned
**Layer:** Post-generation (runs after handwriting generator)
**Model:** `gpt-4o` for image director agent (configurable via model registry)
**Image Model:** `gemini-2.5-flash-image` via `google-genai` SDK (v1.65.0)
**Framework:** LangGraph node (not a ReAct agent — single LLM call with structured output)

An LLM-powered image director agent that reads a completed lesson plan, decides what 3 images would best support the lesson's activities, writes optimized image generation prompts, generates the images via Gemini, uploads to S3, and injects image URLs into the lesson markdown in the HTTP response.

Images generate on every lesson production (initial + modifications). The feedback collector is bypassed. Gemini generation runs as a fire-and-forget background task — the response returns immediately with pre-known S3 URLs that resolve once images finish uploading (~10-15s).

A companion PDF export feature reads `state.lesson_markdown` directly and renders via `weasyprint` with emoji font support.

---

## Architecture Context

```
                FROM HANDWRITING GENERATOR
                (lesson markdown complete)
                           │
                           ▼
┌──────────────────────────────────────────────────────────┐
│              Assembly Node                               │
│                                                          │
│  1. Compute pre-known S3 URLs using thread_id            │
│     s3://l4c-videos/images/{thread_id}/img_{n}.jpg       │
│  2. Store URLs in state.image_urls                       │
│  3. Pass lesson through (no modification yet)            │
│  4. Lesson delivered to user immediately                 │
└──────────────────────┬───────────────────────────────────┘
                       │
                       ▼
┌──────────────────────────────────────────────────────────┐
│         Image Director Agent (THIS SPEC)                 │
│                                                          │
│  Reads: lesson_markdown + handwriting_params from state  │
│  LLM call: gpt-4o with structured output → ImagePlan    │
│                                                          │
│  Decides:                                                │
│  - What 3 images the lesson needs                        │
│  - Full generation prompt for each                       │
│  - Where each image goes (which section)                 │
│  - Alt text for accessibility                            │
│                                                          │
│  Then (no LLM):                                          │
│  - Generates 3 images in parallel via Gemini API         │
│  - Uploads to pre-known S3 URLs                          │
│  - Sends WebSocket events with URLs + placements         │
└──────────────────────────────────────────────────────────┘
```

### End-to-End Flow

```
1. Generator produces lesson markdown (existing, untouched)
2. Assembly node computes pre-known S3 URLs, stores in state
3. Lesson text delivered to user via existing response path
4. Image director agent runs asynchronously:
   a. LLM reads lesson → outputs ImagePlan (3 images)
   b. 3x parallel Gemini API calls → 3 images
   c. 3x parallel S3 uploads
   d. WebSocket event per image: {url, placement, alt_text}
5. Frontend receives events, injects images into rendered lesson
```

---

## Key Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Separate node vs. modify generator | Separate node | Generator is 300+ lines, well-tested, zero risk of breaking existing evals |
| LLM agent vs. templates for prompts | LLM agent | Templates are rigid; agent reads actual lesson content, produces contextually relevant prompts. Self-maintaining as lesson types expand |
| Image count | Fixed at 3 | Enough for pedagogical value, not so many it slows delivery. Configurable later |
| Pre-known URLs | `images/{thread_id}/img_{n}.jpg` | Decouples text delivery from image generation — no coordination needed |
| Async delivery | WebSocket events | User sees lesson immediately; images appear as ready. No blocking |
| Image model | `gemini-2.5-flash-image` | Already proven in user's existing image generation workflow |
| PDF rendering | Backend `weasyprint` | Consistent print layout with proper float/column CSS, independent of browser |
| S3 bucket | `l4c-videos` (existing) | Reuse existing bucket, add `images/` prefix |
| Director model | `gpt-4o` | Needs to understand lesson pedagogy to pick the right images. Swappable via model registry |

---

## Schemas

### ImageRequest

```
ImageRequest:
    prompt: str           — Full image generation prompt (verbose, explicit)
    placement: str        — Section header to place image after (e.g., "Model, Explain & Engage")
    alt_text: str         — Accessible description for screen readers
    pedagogical_role: str — Why this image exists (for traceability, future eval use)
```

### ImagePlan

```
ImagePlan:
    images: list[ImageRequest]  — Exactly 3 items
```

### GraphState Additions

| Field | Type | Purpose |
|-------|------|---------|
| `lesson_markdown` | `Optional[str]` | Latest lesson content — set by `handwriting_generator_node` on every run |
| `image_requests` | `Optional[list[dict]]` | Image director's output (ImagePlan serialized) |
| `image_urls` | `Optional[list[str]]` | Pre-computed S3 URLs for the 3 images |

---

## Image Director System Prompt

The agent's system prompt has four sections: role, educational design principles, image generation prompt rules, and output rules.

### Full System Prompt

```
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
- pedagogical_role: One sentence on why this image exists
```

### User Message Template

```
Here is the lesson plan to illustrate:

Grade: {grade}
Letter: {letter}
Student Level: {student_level}

---

{lesson_markdown}
```

---

## Image Generation Service

### API Integration

Uses the `google-genai` Python SDK (same pattern as the user's existing `generate-image.py` script).

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
- Resolution: `512px` (fast generation, good enough for print at worksheet size)
- Prompt prefix: `"No text, no words, no letters anywhere in the image. "`

### Parallel Generation

All 3 images are generated concurrently using `asyncio.gather()` (or `concurrent.futures.ThreadPoolExecutor` if the SDK is sync-only). Expected wall time: 10-15 seconds for all 3.

---

## S3 Storage

### Bucket & Path Convention

| Item | Value |
|------|-------|
| Bucket | `l4c-videos` |
| Path pattern | `images/{thread_id}/img_{n}.jpg` |
| Example | `images/abc-123-def/img_1.jpg` |
| Public URL | `https://l4c-videos.s3.amazonaws.com/images/{thread_id}/img_1.jpg` |

### Upload Configuration

- Content type: `image/jpeg`
- ACL: `public-read` (images must be accessible via URL in markdown)
- Cache-Control: `max-age=31536000` (immutable — thread_id makes each path unique)

### Pre-Known URLs

The Assembly node computes URLs **before** images exist:

```
For thread_id "abc-123":
  img_1 → https://l4c-videos.s3.amazonaws.com/images/abc-123/img_1.jpg
  img_2 → https://l4c-videos.s3.amazonaws.com/images/abc-123/img_2.jpg
  img_3 → https://l4c-videos.s3.amazonaws.com/images/abc-123/img_3.jpg
```

The image generation service uploads to these exact paths. The frontend renders `<img>` tags that resolve once uploads complete.

---

## WebSocket Image Events

### Event Format

After each image is uploaded to S3, send a WebSocket message:

```
{
  "type": "image_ready",
  "thread_id": "abc-123",
  "image": {
    "url": "https://l4c-videos.s3.amazonaws.com/images/abc-123/img_1.jpg",
    "placement": "Model, Explain & Engage",
    "alt_text": "Lowercase letter d formation guide with numbered stroke order"
  }
}
```

### Frontend Handling

1. On receiving `image_ready` event, find the section header matching `placement` in the rendered lesson
2. Insert `<img src={url} alt={alt_text}>` after that section header
3. Use a fade-in animation so images appear smoothly
4. Show a subtle skeleton/placeholder in each section until the image arrives

---

## Graph Changes

### Updated Flow (Handwriting Path Only)

```
routing_agent → param_agent → handwriting_generator → image_assembly → image_director → END
```

Images generate on **every** generator invocation (initial generation AND modifications). No finalize/approval step required. The feedback collector is bypassed.

### Node Definitions

**handwriting_generator** — ReAct agent (existing, modified)
- Saves last AI message content to `state.lesson_markdown` on every run
- Still tracks `lesson_finalized` via `finalize_lesson` tool (unused by routing currently)

**image_assembly** — Pure function (no LLM)
- Reads `thread_id` from `RunnableConfig`
- Computes 3 pre-known S3 URLs
- Writes `image_urls` to state

**image_director** — LLM + API calls (async node)
- Reads `state.lesson_markdown` + `handwriting_params`
- Calls gpt-4o with structured output → `ImagePlan`
- Kicks off Gemini generation as fire-and-forget background task (`asyncio.create_task`)
- Returns `image_requests` to state immediately

### Entry Routing

Simplified: if `handwriting_params` is set → `handwriting_generator`, otherwise → `routing_agent`. No finalized/feedback checks.

### Routing Logic

After `handwriting_generator`:
- Always → `image_assembly` (unconditional edge, not conditional)

After `image_assembly`:
- Always → `image_director`

After `image_director`:
- Always → END

---

## PDF Export

### Backend Endpoint

```
POST /api/v1/chat/{thread_id}/export-pdf
```

**Response:** PDF file download (Content-Type: `application/pdf`)

### How It Works

1. Endpoint receives `thread_id`
2. Fetch lesson messages from conversation history (existing `ChatHistoryService`)
3. Extract the assistant's lesson markdown (last long assistant message)
4. Fetch image URLs from S3 (using the `images/{thread_id}/` prefix)
5. Render markdown → HTML with embedded `<img>` tags
6. Apply print-optimized CSS (two-column layout where images float right)
7. Convert HTML → PDF via `weasyprint`
8. Return PDF as file download

### Print CSS Highlights

- Images float right with `max-width: 200px` to avoid adding pages
- Section banners are thin horizontal strips
- Writing lines (top, mid, baseline) are preserved at correct proportions
- Page breaks avoided mid-section (`break-inside: avoid`)
- Header/footer with lesson title and page number

### Dependencies

Add `weasyprint` to `requirements.txt`. Note: `weasyprint` requires system libraries (`libpango`, `libcairo`) — add to Dockerfile.

---

## Frontend Changes

### MarkdownRenderer.jsx

- Add image styling: `max-width: 300px`, centered or right-aligned
- Add placeholder skeleton for images that haven't loaded yet
- Handle `image_ready` WebSocket events — inject images into the rendered lesson at the correct placement point

### Export Button

- Add "Export PDF" button below the lesson plan
- Calls `POST /api/v1/chat/{thread_id}/export-pdf`
- Triggers browser file download

---

## Evaluation (Rule-Based Unit Tests)

No LLM judge — all tests use mocks and assertions.

### Test Categories

| Test | What It Verifies | LLM Needed? |
|------|------------------|-------------|
| `test_image_plan_schema_valid` | `ImagePlan` Pydantic model accepts valid data, rejects invalid | No |
| `test_image_plan_exactly_3` | LLM output (mocked) always produces exactly 3 images | No |
| `test_image_plan_has_required_fields` | Each `ImageRequest` has prompt, placement, alt_text, pedagogical_role | No |
| `test_image_prompt_contains_white_bg` | Every generated prompt includes "white background" | No |
| `test_image_prompt_contains_no_text` | Every generated prompt includes "no text, no words, no letters" | No |
| `test_s3_upload_url_format` | Uploaded URL matches `images/{thread_id}/img_{n}.jpg` pattern | No |
| `test_s3_upload_content_type` | Upload uses `image/jpeg` content type | No |
| `test_assembly_computes_urls` | Assembly node produces 3 URLs with correct thread_id | No |
| `test_assembly_url_pattern` | URLs follow `https://l4c-videos.s3.amazonaws.com/images/{id}/img_{n}.jpg` | No |
| `test_gemini_call_shape` | Mocked Gemini client called with correct model, modalities, config | No |
| `test_gemini_parallel_execution` | All 3 image gen calls run concurrently (timing or mock assertion) | No |
| `test_websocket_event_format` | WebSocket message matches `{type, thread_id, image: {url, placement, alt_text}}` | No |
| `test_graph_node_order` | Image assembly runs after generator, image director runs after assembly | No |
| `test_pdf_endpoint_returns_pdf` | Export endpoint returns `Content-Type: application/pdf` | No |
| `test_pdf_contains_images` | Generated PDF HTML includes `<img>` tags with S3 URLs | No |

### Running Tests

```bash
docker compose exec backend pytest tests/unit/test_image_generation.py -v
docker compose exec backend pytest tests/unit/test_pdf_export.py -v
```

### Done When

- [ ] All unit tests pass
- [ ] Image director produces valid `ImagePlan` for a real lesson (manual test)
- [ ] 3 images appear in S3 under `images/{thread_id}/`
- [ ] WebSocket events arrive at frontend with correct placement data
- [ ] Images render in the chat lesson view
- [ ] PDF export downloads a file with embedded images
- [ ] Existing handwriting generator evals still pass (zero regression)

---

## Implementation Files

### New Files

| File | Purpose |
|------|---------|
| `app/services/image_service.py` | Gemini image generation + S3 upload service |
| `app/graph/nodes/image_assembly.py` | Assembly node — computes pre-known URLs via `RunnableConfig` |
| `app/graph/nodes/image_director.py` | Image director agent — gpt-4o structured output → ImagePlan, then parallel Gemini generation |
| `app/schemas/image.py` | `ImageRequest`, `ImagePlan` Pydantic models with exactly-3 validator |
| `app/routers/export.py` | PDF export endpoint (`POST /api/v1/chat/{thread_id}/export-pdf`) |
| `tests/unit/test_image_generation.py` | 16 unit tests for schemas, S3, assembly, Gemini call shape, graph order |
| `tests/unit/test_pdf_export.py` | 6 unit tests for HTML building, text extraction, PDF endpoint |

### Modified Files

| File | Changes |
|------|---------|
| `app/graph/state.py` | Added `lesson_markdown`, `image_requests`, `image_urls` fields |
| `app/graph/graph.py` | Added `image_assembly` + `image_director` nodes; simplified routing: generator → assembly → director → END; simplified entry_router |
| `app/main.py` | Registered `export.router` on protected routes |
| `app/schemas/chat.py` | Added `ImageReadyEvent` schema and `images` field to `ChatMessageResponse` |
| `app/services/chat_service.py` | `_inject_images_into_markdown()` — places image tags after matching section headers; includes `images` in response |
| `frontend/src/components/MarkdownRenderer.jsx` | Added `img` component with responsive styling + lazy loading |
| `frontend/src/components/Chatbot2.jsx` | Added centered Export PDF button, `hasLessonImages` state, `handleExportPdf()` handler |
| `frontend/src/api/index.js` | Added `chat2.exportPdf(threadId)` method with blob download |
| `requirements.txt` | Added `weasyprint>=62.0`, `markdown>=3.5.0` |
| `Dockerfile` | Added system deps for WeasyPrint + `fonts-noto-color-emoji` for PDF emoji rendering |
| `docker-compose.yml` | Added `~/.aws:/root/.aws:ro` volume mount for S3 access in local dev |

---

## Implementation TODO

The coding agent should complete these tasks in order. Check off each when done.

### Phase 1: Schemas & State (do first — other phases depend on this)

- [ ] Create `app/schemas/image.py` with `ImageRequest` and `ImagePlan` Pydantic models
- [ ] Add `image_requests: Optional[list[dict]]` and `image_urls: Optional[list[str]]` to `GraphState` in `app/graph/state.py`
- [ ] Write `tests/unit/test_image_generation.py` — schema validation tests (`test_image_plan_schema_valid`, `test_image_plan_exactly_3`, `test_image_plan_has_required_fields`)
- [ ] Run schema tests — all must pass before proceeding

### Phase 2: Image Service (S3 + Gemini)

- [ ] Create `app/services/image_service.py` with:
  - `generate_image(prompt, aspect_ratio, resolution)` — calls Gemini API, returns PIL Image
  - `upload_to_s3(image_bytes, s3_key)` — uploads JPEG to `l4c-videos` bucket
  - `generate_and_upload(prompt, s3_url)` — combines both
  - `generate_all(image_requests, thread_id)` — parallel generation of all 3
- [ ] Add tests: `test_gemini_call_shape`, `test_s3_upload_url_format`, `test_s3_upload_content_type`, `test_gemini_parallel_execution`
- [ ] Run service tests — all must pass before proceeding

### Phase 3: Graph Nodes

- [ ] Create `app/graph/nodes/image_assembly.py` — computes pre-known S3 URLs, writes to state
- [ ] Create `app/graph/nodes/image_director.py` — LLM call with system prompt (from spec), structured output, then calls image service
- [ ] Add tests: `test_assembly_computes_urls`, `test_assembly_url_pattern`, `test_graph_node_order`
- [ ] Run node tests — all must pass before proceeding

### Phase 4: Graph Wiring

- [ ] Add `image_assembly` and `image_director` nodes to `app/graph/graph.py`
- [ ] Update routing: `handwriting_generator` → `image_assembly` → `image_director` → `feedback_collector`
- [ ] Verify existing handwriting generator evals still pass (zero regression):
  ```bash
  docker compose exec backend pytest tests/evals/test_handwriting_generator.py -v
  ```
- [ ] Run full unit test suite

### Phase 5: WebSocket Events

- [ ] Add `image_ready` WebSocket event emission in `image_director` node after each S3 upload
- [ ] Add test: `test_websocket_event_format`
- [ ] Test manually: generate a lesson, verify 3 WebSocket events arrive

### Phase 6: Frontend

- [ ] Update `MarkdownRenderer.jsx` — add image styling (`max-width: 300px`, centered) and placeholder skeletons
- [ ] Update `Chatbot2.jsx` — handle `image_ready` WebSocket events, inject images at correct placement
- [ ] Add "Export PDF" button below lesson content
- [ ] Test manually: generate a lesson, verify images appear in chat

### Phase 7: PDF Export

- [ ] Add `weasyprint` to `requirements.txt`
- [ ] Add system dependencies to Dockerfile (`libpango1.0-dev`, `libcairo2-dev`, etc.)
- [ ] Create `app/routers/export.py` with `POST /api/v1/chat/{thread_id}/export-pdf`
- [ ] Register router in `app/main.py`
- [ ] Add tests: `test_pdf_endpoint_returns_pdf`, `test_pdf_contains_images`
- [ ] Test manually: export a lesson with images as PDF, verify images appear and layout is clean

### Phase 8: Rebuild & Integration Test

- [ ] `docker compose down && docker compose up -d --build`
- [ ] `docker compose exec backend python scripts/init_db.py`
- [ ] Run all unit tests:
  ```bash
  docker compose exec backend pytest tests/unit/test_image_generation.py tests/unit/test_pdf_export.py -v
  ```
- [ ] Run existing evals to verify zero regression:
  ```bash
  docker compose exec backend pytest tests/evals/ -v
  ```
- [ ] Manual end-to-end: start a conversation, request a handwriting lesson, verify images appear, export PDF

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
| Not all images in PDF | `_build_html()` h2 matching fragile | Known issue — will be fixed by v2 generator-driven placement |
| Emojis missing in PDF | Container lacks emoji fonts | Added `fonts-noto-color-emoji` to Dockerfile |

---

## Open Questions

1. Should image generation be gated behind a feature flag so it can be disabled in production until proven stable?
2. Should we add Langfuse tracing to the image director agent for cost/latency monitoring?
3. For non-handwriting lesson types (vocabulary, idea generation) — should the image director also run, or only for handwriting?

---

## v2 Redesign: Generator-Driven Image Placement (Planned)

### Problem
The current gpt-4o image director call is expensive (~$0.03 + 10-15s), fragile (section header matching often fails), and redundant (generator already knows lesson structure).

### Proposed Design
1. **Generator prompt** includes instruction to place image placeholders: `![description](IMAGE_1)`, `![description](IMAGE_2)`, `![description](IMAGE_3)`
2. Generator outputs lesson with placeholders baked into the markdown
3. **Assembly node** replaces `IMAGE_N` tokens with pre-known S3 URLs in `lesson_markdown`
4. **Image director simplified** — extracts alt text descriptions from placeholders as Gemini prompts. No gpt-4o call.

### What This Eliminates
- The gpt-4o planning call entirely (~$0.03/lesson, ~10-15s)
- `ImagePlan` structured output schema
- `IMAGE_DIRECTOR_SYSTEM_PROMPT` (large prompt)
- `_inject_images_into_markdown()` in chat_service.py
- Fragile h2 matching in PDF `_build_html()`

### Files to Change
1. `app/graph/agents/handwriting_generator.py` — add image placeholder instructions to prompt
2. `app/graph/nodes/image_assembly.py` — replace `IMAGE_N` tokens with S3 URLs in `state.lesson_markdown`
3. `app/graph/nodes/image_director.py` — extract descriptions from placeholders, send to Gemini (no LLM)
4. `app/services/chat_service.py` — remove `_inject_images_into_markdown()`
5. `app/routers/export.py` — simplify `_build_html()` (images already in markdown)
6. Tests — update accordingly

---

## Verification

### Unit Tests
```bash
docker compose exec backend pytest tests/unit/test_image_generation.py tests/unit/test_pdf_export.py -v
```

### Expected Output
- [ ] 22 tests pass (16 image generation + 6 PDF export)
- [ ] Zero regression on existing tests: `docker compose exec backend pytest tests/unit/ -v`

### Health Check
```bash
curl -s http://localhost:8000/api/v1/health
```
Expected: `{"status": "ok"}`

---

## Spec Revisions

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-03-03 | Initial draft |
| 1.0 | 2026-03-03 | Implementation complete — all 22 tests passing. Changed from WebSocket events to image data in HTTP response (ADR-001). |
| 1.1 | 2026-03-04 | Fixed PIL/Pydantic Image bug, S3 credential handling, null safety. Added `lesson_markdown` to state. Simplified routing: always generate images (no finalize gate), bypassed feedback collector. Added emoji font to Dockerfile. Centered Export PDF button. Documented v2 redesign plan. |
