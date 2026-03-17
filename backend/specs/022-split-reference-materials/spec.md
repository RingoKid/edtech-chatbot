# Spec 022: Split Reference Materials + Update Form D

## Status: Planned

## Problem

All handwriting reference forms (A through H, plus Training Codes and 3 grade-specific Form C examples) are consolidated in a single 856-line mega-file (`handwriting_reference.md`). When Dr. Farrow updates an individual form — like the Form D update she sent on Mar 11, 2026 — we must manually update both the mega-file and the original source doc. This creates maintenance drift and makes updates error-prone.

Additionally, Dr. Farrow's updated Form D adds 3 new activities and rewords 1 existing activity that need to be incorporated.

## Solution

1. **Split the mega-file** into individual form files in a new `handwriting/` directory
2. **Rewrite `load_reference_materials()`** to assemble from individual files at runtime
3. **Update Form D** with Dr. Farrow's new activities (Sound Echo, Word Sound Echo, Sound Check) and reworded Sound Detective
4. **Point eval script** to the new file locations

## Implementation Notes

- Use MCP tools (Read, Glob, Grep) to read the mega-file and extract each section by its `## FORM` header
- Preserve exact content — existing evals validate verbatim Form B text and Form F verbal cues

---

## Current Architecture

### Mega-file structure (`handwriting_reference.md`, 856 lines)

| Section | Lines | Header |
|---------|-------|--------|
| Training Codes | 1-47 | `# Handwriting & Spelling Reference Materials` + `## Training Codes` |
| Form B | 49-96 | `## FORM B: Lesson Structure` |
| Form A | 98-109 | `## FORM A: Possible Objectives` |
| Form C PreK | 111-254 | `## FORM C: PreK Example Output` |
| Form C K | 256-414 | `## FORM C: K Example Output` |
| Form C 1st | 416-584 | `## FORM C: 1st Example Output` |
| Form D | 586-643 | `## FORM D: Scaffolded Activities` |
| Form E | 645-661 | `## FORM E: Evidence-Based Practices` |
| Form F | 663-724 | `## FORM F: Sequence Verbal Cues` |
| Form G | 726-802 | `## FORM G: Phoneme Gestures` |
| Form H | 804-856 | `## FORM H: Modification Examples` |

### Current load flow

```
handwriting_generator.py:load_reference_materials(grade)
  → reads entire handwriting_reference.md
  → splits on "\n## " headers
  → filters out non-matching Form C sections
  → returns filtered content as single string
  → injected into {reference_materials} in system prompt
```

### Consumers of form content

| Consumer | File | What it reads |
|----------|------|---------------|
| Generator prompt | `app/graph/agents/handwriting_generator.py` | Mega-file (all forms) |
| Eval script | `scripts/run_scaffolding_evals.py` (lines 55-56) | Old individual files for Form D and Form B |

---

## Target Architecture

### New directory

```
backend/prompt/reference_materials/handwriting/
  training-codes.md
  form-a-objectives.md
  form-b-lesson-structure.md
  form-c-prek.md
  form-c-k.md
  form-c-1st.md
  form-d-scaffolded-activities.md   ← UPDATED with new activities
  form-e-best-practices.md
  form-f-verbal-cues.md
  form-g-phoneme-gestures.md
  form-h-modifications.md
```

### New load flow

```
handwriting_generator.py:load_reference_materials(grade)
  → reads individual form files from handwriting/ directory
  → inserts only the matching form-c-{grade}.md
  → joins with "\n\n---\n\n" separator
  → returns assembled string
  → injected into {reference_materials} (same template, same output)
```

---

## Form D Updates

### New activities (from Dr. Farrow's Dropbox update, Mar 11 2026)

Source: `~/Library/CloudStorage/Dropbox/Handwriting & Spelling (Transcription) AI Codes/Supplementary Forms/FORM D Scaffolded Activities .docx` (1.6 MB, modified Mar 11)

| Activity | Section | Description | Level | Grade Tag (inferred from Rules 13-18) |
|----------|---------|-------------|-------|---------------------------------------|
| **Sound Echo** | Review & Connect | Teacher says sound, children repeat. Echo routine for hearing, memory, producing sounds accurately. | low-level | (Grades: PreK, K) |
| **Word Sound Echo** | Model, Explain, Engage | Children repeat a word that begins with the target sound, then pronounce the first sound in isolation (e.g., octopus /o/). | low-level | (Grades: PreK, K) |
| **Sound Check** | Model, Explain, Engage | Teacher says a sound. Children decide if the sound is the target sound using thumbs up/down or lifting a picture that represents the target sound. | low-level | (Grades: PreK, K) |

### Modified activity

| Activity | Section | Change |
|----------|---------|--------|
| **Sound Detective** | Review & Connect | Reworded: "The teacher says a sound. Tells children to get ready to hunt. Teacher says a word that has that sound in the beginning, middle, or end. Children must point to the first, middle, or second box to indicate where they hear the sound." Stays (middle-level) (Grades: K, 1st). |

### Grade tag rationale

Grade tags are inferred from Rules 13-18 in the system prompt (same method used for all existing Form D tags — see commit `d4dc20c`):
- All 3 new activities are basic echo/identification tasks → appropriate for PreK and K
- Sound Detective requires positional awareness (beginning/middle/end) → stays K, 1st
- Rule 17 (Content Scope): PreK = beginning sounds only, K = beginning + ending, 1st = medial vowels
- Rule 18 (Prior Knowledge): PreK = teach from scratch, K = some knowledge assumed

---

## Implementation Steps

### Step 1: Create individual form files

Extract each section from the mega-file into its own file in `backend/prompt/reference_materials/handwriting/`. Each file:
- Starts with its `## FORM X:` header
- Ends with content (no trailing `---` separator — the join handles that)
- Preserves exact whitespace and formatting

### Step 2: Update Form D

In `form-d-scaffolded-activities.md`:
- Add **Sound Echo** after existing Review & Connect activities header (before Tap that sound)
- Update **Sound Detective** description
- Add **Word Sound Echo** and **Sound Check** after Sound Spark in Model, Explain, Engage section

### Step 3: Rewrite `load_reference_materials()` in `handwriting_generator.py`

Replace path constants and function:

```python
HANDWRITING_DIR = REFERENCE_MATERIALS_DIR / "handwriting"

GRADE_TO_FORM_C_FILE = {
    "PreK": "form-c-prek.md",
    "K": "form-c-k.md",
    "1st": "form-c-1st.md",
}

COMMON_FORM_FILES = [
    "training-codes.md",
    "form-b-lesson-structure.md",
    "form-a-objectives.md",
    # Form C inserted at runtime (position 3)
    "form-d-scaffolded-activities.md",
    "form-e-best-practices.md",
    "form-f-verbal-cues.md",
    "form-g-phoneme-gestures.md",
    "form-h-modifications.md",
]
```

Assembly: read each file, insert grade-specific Form C at index 3, join with `"\n\n---\n\n"`.

### Step 4: Update eval script paths

```python
# scripts/run_scaffolding_evals.py lines 55-56
FORM_D_PATH = "prompt/reference_materials/handwriting/form-d-scaffolded-activities.md"
FORM_B_PATH = "prompt/reference_materials/handwriting/form-b-lesson-structure.md"
```

### Step 5: Delete mega-file

Remove `backend/prompt/reference_materials/handwriting_reference.md`.

---

## Verification

```bash
# Rebuild
docker compose down && docker compose up -d --build
docker compose exec backend python scripts/init_db.py

# 1. Smoke test — assembled output structure
docker compose exec backend python -c "
from app.graph.agents.handwriting_generator import load_reference_materials
out = load_reference_materials('K')
print(f'Length: {len(out)} chars')
for check in ['FORM B:', 'FORM C: K', 'FORM D:', 'Sound Echo', 'Word Sound Echo', 'Sound Check', 'FORM F:', 'FORM H:']:
    print(f'  {check}: {check in out}')
print(f'  PreK Form C absent: {\"FORM C: PreK\" not in out}')
print(f'  1st Form C absent: {\"FORM C: 1st\" not in out}')
"

# 2. Verbatim + verbal cues evals (catch content drift from split)
docker compose exec backend pytest tests/evals/test_handwriting_generator.py::TestVerbatimCheck -v
docker compose exec backend pytest tests/evals/test_handwriting_generator.py::TestVerbalCues -v

# 3. Eval script still loads forms correctly
docker compose exec -e GIT_SHA=$(git rev-parse --short HEAD) backend python scripts/run_scaffolding_evals.py --list
```

---

## Files Modified

| File | Change |
|------|--------|
| `backend/app/graph/agents/handwriting_generator.py` | Rewrite `load_reference_materials()`, update path constants, remove `GRADE_TO_FORM_C_HEADER` |
| `backend/scripts/run_scaffolding_evals.py` | Update `FORM_D_PATH` and `FORM_B_PATH` (lines 55-56) |

## Files Created

| File | Content |
|------|---------|
| `backend/prompt/reference_materials/handwriting/training-codes.md` | Extracted from mega-file lines 1-47 |
| `backend/prompt/reference_materials/handwriting/form-a-objectives.md` | Extracted from mega-file lines 98-109 |
| `backend/prompt/reference_materials/handwriting/form-b-lesson-structure.md` | Extracted from mega-file lines 49-96 |
| `backend/prompt/reference_materials/handwriting/form-c-prek.md` | Extracted from mega-file lines 111-254 |
| `backend/prompt/reference_materials/handwriting/form-c-k.md` | Extracted from mega-file lines 256-414 |
| `backend/prompt/reference_materials/handwriting/form-c-1st.md` | Extracted from mega-file lines 416-584 |
| `backend/prompt/reference_materials/handwriting/form-d-scaffolded-activities.md` | Extracted from mega-file lines 586-643 + new activities |
| `backend/prompt/reference_materials/handwriting/form-e-best-practices.md` | Extracted from mega-file lines 645-661 |
| `backend/prompt/reference_materials/handwriting/form-f-verbal-cues.md` | Extracted from mega-file lines 663-724 |
| `backend/prompt/reference_materials/handwriting/form-g-phoneme-gestures.md` | Extracted from mega-file lines 726-802 |
| `backend/prompt/reference_materials/handwriting/form-h-modifications.md` | Extracted from mega-file lines 804-856 |

## Files Deleted

| File | Reason |
|------|--------|
| `backend/prompt/reference_materials/handwriting_reference.md` | Replaced by individual files |

## What Does NOT Change

- `DEFAULT_HANDWRITING_GENERATOR_PROMPT` template — still receives `{reference_materials}`
- `app/langfuse/criteria.py` — hardcoded verbatim strings are eval ground truth
- Old files in `Handwriting & Spelling (Transcription) AI Codes/` — Dr. Farrow's originals
- `handwriting-spelling-standards.md` — already standalone
- System prompt Rules 1-19 — no changes needed
