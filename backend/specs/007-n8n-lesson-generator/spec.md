# 007: n8n Lesson Generator Workflow

## Overview

**Version:** 0.1 — Single-shot lesson generation with full context
**Status:** Implemented
**Last Updated:** 2026-01-11

A minimal n8n workflow that generates handwriting & spelling lesson plans. All reference forms included in prompt (no filtering). This is the foundation for iterative prompt engineering experiments.

**Scope:** Webhook → Validate → Build Prompt → LLM → Respond

---

## Documentation Sources (REQUIRED)

Before implementing, use Context7 MCP to look up current documentation:

| Library | Topics to Query |
|---------|-----------------|
| `n8n` | Webhook node, Code node, IF node, HTTP Request node, Respond to Webhook, API endpoints |
| `openai` | Chat completions API, message format, temperature |

Do NOT implement from memory. Fetch current docs.

> **Note:** The native n8n OpenAI nodes have limitations. Query HTTP Request node docs as a fallback for direct API calls.

---

## Input/Output Contract

### Request

```
POST http://localhost:5678/webhook/generate
Content-Type: application/json
```

```json
{
  "grade": "PreK",
  "letter": "z"
}
```

| Field | Type | Required | Values |
|-------|------|----------|--------|
| `grade` | string | Yes | `PreK`, `Kindergarten`, `1st` |
| `letter` | string | Yes | Any letter a-z or digraph |

### Response (Success)

```json
{
  "success": true,
  "grade": "PreK",
  "letter": "z",
  "lesson": "Handwriting & Spelling Lesson\n\nA. Standards..."
}
```

### Response (Validation Error)

```json
{
  "success": false,
  "error": "Missing required fields",
  "required": ["grade", "letter"],
  "missing": ["letter"]
}
```

---

## Workflow Nodes

```
┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
│ Webhook  │───►│    IF    │───►│   Code   │───►│   HTTP   │───►│ Respond  │
│ Trigger  │    │ Validate │    │  Prompt  │    │ Request  │    │  JSON    │
└──────────┘    └────┬─────┘    └──────────┘    │ (OpenAI) │    └──────────┘
                     │                          └──────────┘
                     ▼ (missing fields)
               ┌──────────┐
               │ Respond  │
               │  Error   │
               └──────────┘
```

### Node 1: Webhook Trigger

- **Method:** POST
- **Path:** `/generate`
- **Authentication:** None (v0.1)

### Node 2: IF (Validate)

Check that both `grade` and `letter` exist in request body.

- **True branch:** Continue to prompt building
- **False branch:** Return error response

### Node 3: Code (Build Prompt)

Assemble the full prompt from form content.

**Inputs:** `grade`, `letter` from webhook body

**Outputs:** `systemPrompt`, `userPrompt`

### Node 4: OpenAI (via HTTP Request)

> **Implementation Note:** Uses `n8n-nodes-base.httpRequest` instead of the native OpenAI node. The LangChain OpenAI node (`@n8n/n8n-nodes-langchain.openAi`) doesn't properly pass custom messages, and the standard OpenAI node has parameter structure issues.

- **Type:** `n8n-nodes-base.httpRequest`
- **URL:** `https://api.openai.com/v1/chat/completions`
- **Authentication:** OpenAI API credential (configured in n8n)
- **Body (JSON expression):**
  ```javascript
  ={{ JSON.stringify({
    model: 'gpt-4o',
    temperature: 0.7,
    messages: [
      { role: 'system', content: $('Build Prompt').item.json.systemPrompt },
      { role: 'user', content: $('Build Prompt').item.json.userPrompt }
    ]
  }) }}
  ```
- **Response path:** `$json.choices[0].message.content`

### Node 5: Respond to Webhook (Success)

Return JSON with lesson content.

**Response Body (expression):**
```javascript
={
  "success": true,
  "grade": "{{ $('Build Prompt').item.json.grade }}",
  "letter": "{{ $('Build Prompt').item.json.letter }}",
  "lesson": {{ JSON.stringify($json.choices[0].message.content) }}
}
```

### Node 5b: Respond to Webhook (Error)

Return JSON with validation error details.

---

## Prompt Assembly

### Structure

```
┌─────────────────────────────────────────────────────────────┐
│ SYSTEM PROMPT                                               │
│                                                             │
│ Role: Structured literacy curriculum expert                 │
│ Knowledge: Science of reading, PreK-1st phonics, Georgia    │
│            Standards of Excellence                          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│ USER PROMPT                                                 │
│                                                             │
│ 1. Form B (Structure Rules)                                 │
│    - Required sections                                      │
│    - Markers and formatting                                 │
│    - Verbatim explanations                                  │
│                                                             │
│ 2. Form D (Activities)                                      │
│    - Activities by section                                  │
│    - Difficulty levels                                      │
│                                                             │
│ 3. Form F (Verbal Cues)                                     │
│    - All letter cues A-Z, a-z                               │
│                                                             │
│ 4. Form C (Example Output)                                  │
│    - Complete example lesson                                │
│                                                             │
│ 5. User Input                                               │
│    - Grade: {grade}                                         │
│    - Letter: {letter}                                       │
│                                                             │
│ 6. Generation Instruction                                   │
│    - Follow Form B structure                                │
│    - Use Form D activities                                  │
│    - Include verbal cues for target letter                  │
└─────────────────────────────────────────────────────────────┘
```

### Token Budget (Estimated)

| Component | Tokens |
|-----------|--------|
| System prompt | ~200 |
| Form B | ~800 |
| Form C | ~2,400 |
| Form D | ~1,900 |
| Form F | ~650 |
| Instructions | ~100 |
| **Total Input** | **~6,050** |
| Output (lesson) | ~2,500 |
| **Total per call** | **~8,550** |

---

## Form Content Reference

### Form Locations

| Form | Path |
|------|------|
| Form B | `backend/prompt/Handwriting & Spelling (Transcription) AI Codes/FORM B-Codes for Lesson Parts Handwriting & Spelling.txt` |
| Form C | `backend/prompt/Handwriting & Spelling (Transcription) AI Codes/FORM C_ Example Handwriting & Spelling Lesson for Output .txt` |
| Form D | `backend/prompt/Handwriting & Spelling (Transcription) AI Codes/Supplementary Forms/FORM D Scaffolded Activities .txt` |
| Form F | `backend/prompt/Handwriting & Spelling (Transcription) AI Codes/Supplementary Forms/Form F_ Sequence Verbal Cues.txt` |

### Form B — Key Requirements

The generated lesson MUST include these verbatim in `[Explanation]` blocks:

| Section | Verbatim Text |
|---------|---------------|
| Review & Connect | "The purpose of this part of the lesson is to start with a quick review of previously learned sounds. Do not use sounds that have not been directly taught. Do not use words that have sounds that have not been directly taught." |
| Model, Explain & Engage | "The purpose of this part of the lesson is to connect a sound or sound patterns that you focused on during your reading block to writing its corresponding grapheme patterns. First, make sure children clearly can distinguish the targeted sound; then, hook that sound to the letter patterns through modeling and explaining the sequence of strokes for letters and correct order of letters." |
| Guided Practice | "The purpose of this part of the lesson is to give children practice writing the letter while supporting proper pencil grip and correct sequence of stroke formation using handwriting lines." |
| Application | "The purpose of this part of the lesson is to facilitate children's spelling of the letter or letter patterns when they hear the sound(s). This supports children's early coordination of matching sound to letter(s) for the purpose of spelling words." |
| Wrap-Up | "The purpose of this part of the lesson is to remind students what they were focused on and provide praise for their accomplishments." |

### Form B — Required Markers

| Marker | Format | Purpose |
|--------|--------|---------|
| Explanation | `[Explanation: ...]` | AI explains lesson parts |
| Teacher Script | `#Teacher Script:` | What teacher says |
| Child Response | `(Children...)` | Expected student responses |
| Teacher Does | `{Teacher...}` | Teacher actions |
| Gesture | `+Gesture:` | Phoneme gesture |
| Verbal Cues | `##Sequence Verbal Cues` | Letter formation |
| Modification | `*Adaptation:` | End-of-lesson prompt |

### Form B — Required Sections

1. Standards (Georgia ELAGSE codes)
2. Objectives
3. Materials
4. Review & Connect
5. Model, Explain & Engage
6. Guided Practice
7. Application
8. Wrap-Up

### Form D — Activities by Section

Include full Form D content. The LLM selects appropriate activities based on:
- Section (Review, Model, Guided Practice, Application)
- Difficulty level (low, middle, high)
- Grade appropriateness

### Form F — Verbal Cues

Include full Form F content (all 52 letters). The LLM uses the cue matching the target letter.

Example for letter z:
- Uppercase Z: "Little line across. Slant down the stairs. Little line across"
- Lowercase z: "Little line across, slant down the stairs, little line across"

### Form C — Example Output

Include full Form C content as a few-shot example. This shows:
- Expected structure
- Proper marker usage
- Verbatim explanation format
- Activity integration

---

## Experiment Tracking

### Directory Structure

```
n8n/
├── workflows/
│   └── lesson-generator-v01.json    # Exported from n8n
├── experiments/
│   └── changelog.md                  # Experiment log
└── outputs/
    └── v01-prek-z.md                 # Sample outputs
```

### After Each Workflow Change

1. Export workflow from n8n UI (Download → JSON)
2. Save as `lesson-generator-v0X.json`
3. Update `changelog.md`
4. Save sample output to `outputs/`
5. Git commit with descriptive message

### changelog.md Template

```markdown
# n8n Lesson Generator - Experiment Log

## v01 - YYYY-MM-DD - Baseline
**Hypothesis:** Basic prompt with all forms can generate acceptable lessons

**Configuration:**
- Model: GPT-4o
- Temperature: 0.7
- Forms: B, C, D, F (full, no filtering)

**Observations:**
- [ ] All required sections present
- [ ] Verbatim explanations included
- [ ] Correct verbal cues for target letter
- [ ] Appropriate activities selected
- Token usage: ___

**Sample:** `outputs/v01-prek-z.md`
```

---

## Testing

### Manual Test

```bash
# Success case
curl -X POST http://localhost:5678/webhook/generate \
  -H "Content-Type: application/json" \
  -d '{"grade": "PreK", "letter": "z"}'

# Missing field case
curl -X POST http://localhost:5678/webhook/generate \
  -H "Content-Type: application/json" \
  -d '{"grade": "PreK"}'
```

### Validation Checklist

**Structure:**
- [ ] Standards section with Georgia ELAGSE codes
- [ ] Objectives section
- [ ] Materials section
- [ ] All 5 lesson sections (Review, Model, Guided, Application, Wrap-Up)

**Verbatim Explanations:**
- [ ] Review & Connect explanation present and exact
- [ ] Model, Explain & Engage explanation present and exact
- [ ] Guided Practice explanation present and exact
- [ ] Application explanation present and exact
- [ ] Wrap-Up explanation present and exact

**Markers:**
- [ ] `[Explanation: ...]` blocks used
- [ ] `#Teacher Script:` sections present
- [ ] `(Children...)` responses included
- [ ] `{Teacher...}` actions included
- [ ] `+Gesture:` for phoneme
- [ ] `##Sequence Verbal Cues` with correct cues
- [ ] `*Adaptation:` prompt at end

**Content:**
- [ ] Verbal cues match target letter from Form F
- [ ] Activities appropriate for grade level
- [ ] Activities match section purpose (from Form D)

### Baseline Test

**Input:** `{grade: "PreK", letter: "z"}`
**Expected:** Output closely matches Form C structure and content

---

## Files Created

| Path | Purpose |
|------|---------|
| `n8n/workflows/lesson-generator-v01.json` | Exported workflow |
| `n8n/experiments/changelog.md` | Experiment tracking |
| `n8n/outputs/` | Sample outputs |

---

## Iteration Path

| Version | Focus | Key Change |
|---------|-------|------------|
| **v0.1** | Baseline | All forms hardcoded, no filtering |
| v0.2 | File loading | Load forms from mounted files |
| v0.3 | Optimization | Filter Form F to target letter only |
| v0.4 | Extended context | Add Form A (objectives), Form H (modifications) |
| v0.5 | Multi-model | Parallel branches for GPT-4o + Claude |
| v0.6 | Observability | Langfuse tracing and scoring |
| v0.7 | Evaluation | LLM-as-Judge with rubrics |

---

## Prerequisites

| Requirement | Purpose |
|-------------|---------|
| Docker with n8n running | Workflow execution |
| OpenAI API key configured in n8n | LLM calls |
| Access to form files | Prompt content |

---

## Notes

- n8n runs at `http://localhost:5678` (from docker-compose)
- OpenAI credentials must be configured in n8n UI before workflow runs
- For v0.1, all form content is hardcoded in the Code node
- Form E (best practices) and Form G (gestures) are PDFs — skipped for v0.1

---

## n8n Workflow Management

### CLI vs API

The n8n CLI is limited for iterative development. Use the REST API for full control.

| Operation | CLI | API | Recommendation |
|-----------|-----|-----|----------------|
| Import | `n8n import:workflow --input=<file>` | `POST /api/v1/workflows` | CLI works |
| List | `n8n list:workflow` | `GET /api/v1/workflows` | CLI works |
| Export | `n8n export:workflow --id=<id>` | `GET /api/v1/workflows/{id}` | Either works |
| Update | ❌ Creates duplicate | `PUT /api/v1/workflows/{id}` | **API only** |
| Delete | ❌ Not available | `DELETE /api/v1/workflows/{id}` | **API only** |
| Activate | ❌ Broken (version errors) | `POST /api/v1/workflows/{id}/activate` | **API only** |

### API Examples

Use the wrapper script at `n8n/api.sh` (handles auth automatically):

```bash
# List workflows
./n8n/api.sh workflows

# Update workflow
./n8n/api.sh workflows/{id} -X PUT \
  -H "Content-Type: application/json" \
  -d @n8n/workflows/lesson-generator-v01.json

# Activate workflow
./n8n/api.sh workflows/{id}/activate -X POST

# Delete workflow
./n8n/api.sh workflows/{id} -X DELETE
```

### Expression Syntax

Use explicit node references for reliability:

```javascript
// Preferred - explicit node reference
$('Build Prompt').item.json.systemPrompt

// Avoid - assumes previous node output
$json.systemPrompt
```

---

## Implementation Lessons Learned

1. **n8n OpenAI nodes have quirks**: The LangChain node is for agent workflows; the standard node has parameter issues. HTTP Request gives full control.

2. **CLI is limited**: Good for initial import, but lacks update/delete. API is essential for iterative development.

3. **Test nodes early**: Before building full workflows, test that nodes behave as expected with your specific configuration.

4. **Expression debugging**: Use test executions in n8n UI to inspect node inputs/outputs when expressions don't evaluate correctly.
