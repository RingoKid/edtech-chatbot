# 014: LLM Judge Evals — Scaffolding Sequencing

## Overview

**Status:** Implemented
**Scope:** Rubric Criterion 1 only — Logical Sequencing of Activities
**Judge Model:** `gpt-5.2` (configurable via `get_chat_model()`)
**Generator Model:** `gpt-4o` (existing handwriting generator)

Two LLM judge evals that assess whether a generated handwriting lesson sequences activities logically — from easier to harder — both within individual sections and across the lesson as a whole.

This spec covers the **first two** of the four scaffolding evals planned in `decisions.md`:
- `scaffolding_within_activity` — Are steps within each section ordered easier → harder?
- `scaffolding_between_activity` — Do earlier sections build skills that later sections depend on?

The remaining two (`scaffolding_gradual_release`, `scaffolding_level_appropriate`) are out of scope for this spec.

---

## Design Decisions

See `decisions.md` and `decisions/001-decoupled-fixtures.md` for full context. Key decisions:

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Fixture-based | Pre-generate lessons, judge saved outputs | Fast eval runs (~seconds), deterministic inputs |
| Scoring approach | Count/classify per item, compute percentage | Structural and explainable, not vibes-based |
| Separate evals | One judge call per criterion per fixture | Independent, parallelizable, clear ownership |
| Judge model | `gpt-5.2` (configurable) | Nuanced pedagogical assessment needs strong model |
| No pytest | Script produces markdown report | Rich reporting with judge reasoning, not just pass/fail |
| Wrap-Up excluded | Section 5 excluded from both evals | Wrap-Up is intentionally a cool-down, not an escalation |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 1: Generate Fixtures                     │
│                  scripts/generate_eval_fixtures.py                │
│                                                                   │
│  Run handwriting generator with varied params                     │
│  Save lesson outputs as JSON to tests/fixtures/                   │
│  One-time cost, re-run only when generator prompt changes         │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────────┐
│                    STEP 2: Run Scaffolding Evals                 │
│                scripts/run_scaffolding_evals.py                   │
│                                                                   │
│  For each fixture:                                                │
│    → Load lesson JSON                                             │
│    → Run within-section judge (LLM call + structured output)      │
│    → Run across-section judge (LLM call + structured output)      │
│    → Compute percentages from structured output                   │
│                                                                   │
│  Generate markdown report:                                        │
│    → Summary table (all fixtures at a glance)                     │
│    → Per-fixture breakdown with pair-level detail                 │
│    → Judge reasoning quoted per item                              │
│    → Save to results/scaffolding_YYYY-MM-DD_HHMMSS.md             │
└─────────────────────────────────────────────────────────────────┘
```

---

## Fixture Generation

### Script

**File:** `scripts/generate_eval_fixtures.py`

Runs the full handwriting generator graph for each param combo and saves the lesson output as JSON.

```bash
# Generate all fixtures (skip existing)
docker compose exec backend python scripts/generate_eval_fixtures.py

# Force regenerate all
docker compose exec backend python scripts/generate_eval_fixtures.py --force
```

### Fixture Param Matrix

A mix of params — some match the example lessons exactly (for calibration), others vary for broader coverage.

| ID | Grade | Letter | Level | Notes |
|----|-------|--------|-------|-------|
| `prek_letter_z_onlevel` | PreK | Z | on-level | Matches Form C example |
| `k_letter_b_struggling` | K | B | struggling | Matches Example Lesson 3 (low) |
| `k_letter_b_onlevel` | K | B | on-level | Matches Example Lesson 1 (high) |
| `k_letter_b_advanced` | K | B | advanced | Same letter, highest level |
| `k_letter_t_onlevel` | K | T | on-level | Different letter, mid grade |
| `k_letter_w_advanced` | K | W | advanced | Complex letter, high level |
| `prek_letter_a_onlevel` | PreK | A | on-level | Simple letter, youngest grade |
| `prek_letter_m_struggling` | PreK | M | struggling | Easy letter, low level |
| `first_letter_e_onlevel` | 1st | E | on-level | Oldest grade |
| `first_letter_r_struggling` | 1st | R | struggling | Oldest grade, low level |
| `first_letter_d_advanced` | 1st | D | advanced | Confusable letter (d/b), high level |
| `k_letter_p_onlevel` | K | P | on-level | Confusable with /b/ |

**Total: 12 fixtures**

### Fixture JSON Schema

**Location:** `tests/fixtures/handwriting_generator/{fixture_id}.json`

```json
{
  "fixture_id": "k_letter_b_onlevel",
  "params": {
    "grade": "K",
    "letter": "B",
    "student_level": "on-level"
  },
  "lesson_output": "**Handwriting & Spelling Lesson**\n\nA. Standards...",
  "generated_at": "2026-02-05T12:00:00Z",
  "generator_model": "gpt-4o",
  "generator_prompt_version": "handwriting-generator:production"
}
```

---

## Eval 1: `scaffolding_within_activity`

### What It Measures

Whether activities/steps within each lesson section (1-4) are ordered from cognitively simpler to more complex. Section 5 (Wrap-Up) is excluded.

### How It Works

1. Judge receives the lesson output + Form D (full text) as reference
2. For each of sections 1-4, judge:
   - Identifies all distinct activities/steps
   - Maps each to a difficulty level (`low`, `middle`, `high`) using Form D
   - For each consecutive pair, judges whether the second is equal or harder difficulty
3. Code computes: `correctly_ordered_pairs / total_pairs × 100`

### Example

```
Section: Review & Connect
  Activities found:
    1. Sound Sparks (low) — "say the sound chorally"
    2. Write that Sound (high) — "write the letter for the sound"
  Pairs:
    [Sound Sparks → Write that Sound] = low → high ✓

Section: Guided Practice
  Activities found:
    1. Magic Finger Write (low) — "trace with finger, no pencil"
    2. Say and Trace (middle) — "trace dotted lines with pencil"
    3. Write and Sound (middle) — "write freely while saying sound"
  Pairs:
    [Magic Finger Write → Say and Trace] = low → middle ✓
    [Say and Trace → Write and Sound] = middle → middle ✓
```

### Pydantic Structured Output

```python
from pydantic import BaseModel
from typing import Literal

class Activity(BaseModel):
    name: str
    difficulty_level: Literal["low", "middle", "high"]
    reasoning: str  # Why this difficulty level, referencing Form D

class ActivityPair(BaseModel):
    from_activity: str
    to_activity: str
    correctly_ordered: bool  # True if to >= from in difficulty
    reasoning: str

class SectionAnalysis(BaseModel):
    section_name: str  # "Review & Connect", "Model, Explain & Engage", etc.
    activities: list[Activity]
    pairs: list[ActivityPair]

class WithinSectionOutput(BaseModel):
    sections: list[SectionAnalysis]  # Sections 1-4 only (exclude Wrap-Up)
    explanation: str  # Overall summary
```

### Score Computation (in code, not LLM)

```python
total_pairs = sum(len(s.pairs) for s in output.sections)
correct_pairs = sum(
    1 for s in output.sections
    for p in s.pairs
    if p.correctly_ordered
)
score = (correct_pairs / total_pairs * 100) if total_pairs > 0 else 0.0
```

### Judge Prompt

**Location:** `tests/evals/rubrics/scaffolding_within_activity.md`

The prompt must include:
1. **Role:** You are an expert in early childhood literacy pedagogy
2. **Task:** Analyze the within-section sequencing of this handwriting lesson
3. **Rubric criterion** (verbatim from rubric): "The activities involved should be sequenced in a logical way, starting with easier skills and building in difficulty both within activities"
4. **Examples from rubric:** The within-activity examples (Sound Sparks → Write that Sound, Magic Finger Write → Say and Trace → Write without tracing)
5. **Form D full text:** The complete activity menu with difficulty labels — this is the judge's reference for mapping activities to levels
6. **Variable substitution:** `{lesson_output}` placeholder for the fixture's lesson text
7. **Instructions:** Identify activities in sections 1-4 only, map each to Form D difficulty, evaluate consecutive pairs

---

## Eval 2: `scaffolding_between_activity`

### What It Measures

Whether activities in later sections build on skills taught in earlier sections. The lesson should show cross-section dependency — earlier activities prime/prepare skills needed for later, harder activities. Section 5 (Wrap-Up) is excluded.

### How It Works

1. Judge receives the lesson output + Form D (full text) as reference
2. Judge identifies cross-section links: activities in sections 2-4 that depend on or build from activities in earlier sections
3. For each link, judge assesses whether the earlier activity genuinely primes the later one
4. Code computes: `correctly_building_links / total_links × 100`

### Example

```
Cross-section links found:
  1. Stretch the Sounds (§2 Model/Explain) → Stretch and Spell (§4 Application) ✓
     "Segmentation practice in §2 is a prerequisite for the spelling
      task in §4, which requires segmenting then writing each sound"

  2. Sound Hunt - identify /b/ position (§2) → Sound-Letter Hunt - write /b/ (§4) ✓
     "Identifying the sound position (perceptual) in §2 feeds into
      writing the sound (productive) in §4"

  3. Letter formation with verbal cues (§2) → Say and Write (§3 Guided Practice) ✓
     "Teacher-modeled formation in §2 is directly practiced
      by children in §3"
```

### Pydantic Structured Output

```python
class CrossSectionLink(BaseModel):
    earlier_section: str  # e.g., "Model, Explain & Engage"
    earlier_activity: str
    later_section: str  # e.g., "Application"
    later_activity: str
    builds_correctly: bool
    reasoning: str  # How the earlier activity primes the later one

class AcrossSectionOutput(BaseModel):
    links: list[CrossSectionLink]  # All identified cross-section dependencies
    explanation: str  # Overall summary of across-section coherence
```

### Score Computation (in code, not LLM)

```python
total_links = len(output.links)
correct_links = sum(1 for l in output.links if l.builds_correctly)
score = (correct_links / total_links * 100) if total_links > 0 else 0.0
```

### Judge Prompt

**Location:** `tests/evals/rubrics/scaffolding_between_activity.md`

The prompt must include:
1. **Role:** You are an expert in early childhood literacy pedagogy
2. **Task:** Analyze the across-section sequencing of this handwriting lesson
3. **Rubric criterion** (verbatim from rubric): "The activities involved should be sequenced in a logical way, starting with easier skills and building in difficulty between activities"
4. **Examples from rubric:** The between-activity examples (Model/Explain stretching → Application spelling; Review sound isolation → Model/Explain letter formation)
5. **Form D full text:** Complete activity menu with difficulty labels
6. **Variable substitution:** `{lesson_output}` placeholder
7. **Instructions:** Identify cross-section dependencies in sections 1-4 only, evaluate whether each link shows genuine skill building

---

## Report Generation

### Script

**File:** `scripts/run_scaffolding_evals.py`

```bash
# Run evals on all fixtures
docker compose exec backend python scripts/run_scaffolding_evals.py

# Run on specific fixture
docker compose exec backend python scripts/run_scaffolding_evals.py --fixture k_letter_b_onlevel

# Use different judge model
docker compose exec backend python scripts/run_scaffolding_evals.py --model gpt-4o
```

### Report Output

**Location:** `tests/evals/results/scaffolding_YYYY-MM-DD_HHMMSS.md`

### Report Format

```markdown
# Scaffolding Eval Results

**Run date:** 2026-02-05 14:30:00
**Judge model:** gpt-5.2
**Generator model:** gpt-4o
**Fixtures evaluated:** 12

---

## Summary

| Fixture | Within | Across | Avg |
|---------|--------|--------|-----|
| prek_letter_z_onlevel | 87.5% (7/8) | 100% (4/4) | 93.8% |
| k_letter_b_struggling | 100% (5/5) | 80.0% (4/5) | 90.0% |
| k_letter_b_onlevel | 75.0% (6/8) | 100% (3/3) | 87.5% |
| ... | ... | ... | ... |
| **Overall Average** | **82.3%** | **88.5%** | **85.4%** |

---

## Detailed Results

### prek_letter_z_onlevel
**Params:** PreK | Letter Z | on-level

#### Within-Section Sequencing: 87.5% (7/8 pairs)

**Review & Connect**
| # | From | To | Ordered? | Reasoning |
|---|------|----|----------|-----------|
| 1 | Sound Sparks (low) | Write that Sound (high) | ✓ | "Vocal production → recall + motor writing" |

**Model, Explain & Engage**
| # | From | To | Ordered? | Reasoning |
|---|------|----|----------|-----------|
| 1 | Sound Hunt (low) | Letter Formation (middle) | ✓ | "Perceptual → motor production" |
| 2 | Letter Formation (middle) | Verbal Cues (middle) | ✓ | "Similar demand, both motor" |

(... continues for Guided Practice, Application)

**Judge Summary:** "The lesson shows strong within-section progression..."

#### Across-Section Sequencing: 100% (4/4 links)

| # | Earlier (Section) | Later (Section) | Builds? | Reasoning |
|---|-------------------|-----------------|---------|-----------|
| 1 | Stretch Sounds (§2) | Stretch & Spell (§4) | ✓ | "Segmentation primes spelling" |
| 2 | Sound Hunt (§2) | Sound-Letter Hunt (§4) | ✓ | "Identify → write" |

**Judge Summary:** "Clear cross-section dependencies..."

---

(... repeats for each fixture)
```

---

## Criteria Registry Updates

Add both new criteria to `CRITERIA_REGISTRY` in `app/langfuse/criteria.py`:

```python
"scaffolding_within_activity": {
    "type": "llm-judge",
    "description": "Checks if activities within each section are ordered easier → harder",
},
"scaffolding_between_activity": {
    "type": "llm-judge",
    "description": "Checks if activities across sections build on earlier skills",
},
```

---

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Pydantic structured output models | ✅ Done | `tests/evals/models.py` |
| Within-section judge rubric | ✅ Done | `tests/evals/rubrics/scaffolding_within_activity.md` |
| Across-section judge rubric | ✅ Done | `tests/evals/rubrics/scaffolding_between_activity.md` |
| Fixture generation script | ✅ Done | `scripts/generate_eval_fixtures.py` |
| Scaffolding eval runner script | ✅ Done | `scripts/run_scaffolding_evals.py` |
| Criteria registry updates | ✅ Done | 2 new `llm-judge` entries in `app/langfuse/criteria.py` |
| Gitignore for fixture JSON | ✅ Done | `.gitignore` updated |
| Fixture generation (12 combos) | ✅ Done | All 12 fixtures generated |
| Full eval run | ✅ Done | Within=83.3%, Across=93.8%, Avg=88.5% (scores vary ~2-5% between runs due to LLM non-determinism) |

## Implementation Files

### New Files

| File | Purpose |
|------|---------|
| `scripts/generate_eval_fixtures.py` | Generate lesson fixtures from handwriting generator |
| `scripts/run_scaffolding_evals.py` | Run both judge evals, produce markdown report |
| `tests/evals/rubrics/scaffolding_within_activity.md` | Judge prompt for within-section eval |
| `tests/evals/rubrics/scaffolding_between_activity.md` | Judge prompt for across-section eval |
| `tests/evals/models.py` | Pydantic models for structured judge output |

### Modified Files

| File | Changes |
|------|---------|
| `app/langfuse/criteria.py` | Add 2 new `llm-judge` criteria to `CRITERIA_REGISTRY` |
| `.gitignore` | Add `backend/tests/fixtures/handwriting_generator/*.json` |

### Generated Files (not committed)

| File | Purpose |
|------|---------|
| `tests/fixtures/handwriting_generator/*.json` | Pre-generated lesson fixtures (12 files) |
| `tests/evals/results/scaffolding_*.md` | Eval reports (one per run) |

---

## Reference Materials for Judge Prompts

Both judge rubric templates use a `{form_d}` placeholder. Form D is loaded from the source markdown file at runtime by `run_scaffolding_evals.py` (single source of truth — not hardcoded in the rubrics).

**Form D source:** `backend/prompt/Handwriting & Spelling (Transcription) AI Codes/Supplementary Forms/FORM D Scaffolded Activities .md`

The rubric examples come from:

**Rubric:** `backend/prompt/Handwriting & Spelling (Transcription) AI Codes/Rubric for Lesson Plan Generator.md` (criterion 1 only — logical sequencing)

The example lessons for calibration context:

**Examples:** `backend/prompt/Handwriting & Spelling (Transcription) AI Codes/Further example lesson plans Transcription.md`

---

## Implementation Notes

- **Use Context7 MCP** to pull latest documentation for LangChain, LangGraph, and Pydantic during implementation
- Use `get_chat_model("gpt-5.2")` from `app/llm/client.py` for judge calls — this keeps model selection going through the existing registry
- Use `model.with_structured_output(PydanticModel)` for judge calls — this is the existing pattern for structured LLM output
- The fixture generation script must run the full graph (routing → params → generation) — follow the flow pattern in `tests/evals/test_handwriting_generator.py`
- Judge rubric templates use two placeholders substituted at runtime: `{form_d}` (loaded from source markdown) and `{lesson_output}` (from fixture JSON)
- Form D is loaded once per eval run from the source markdown file and passed to both judges — not hardcoded in rubric files
- The report script should default to `gpt-5.2` but accept `--model` flag for easy switching
- Fixture JSON files should be gitignored (they contain LLM outputs that vary between runs)
- Report files should be committed per-iteration for tracking progress over time

---

## Verification

### Generate Fixtures
```bash
docker compose exec backend python scripts/generate_eval_fixtures.py
# Expected: 12 JSON files in tests/fixtures/handwriting_generator/
```

### Run Evals
```bash
docker compose exec backend python scripts/run_scaffolding_evals.py
# Expected: Markdown report in tests/evals/results/
```

### Single Fixture Test
```bash
docker compose exec backend python scripts/run_scaffolding_evals.py --fixture k_letter_b_onlevel
# Expected: Report with only one fixture evaluated
```

### Verify Report Contents
The report should contain:
- Summary table with all fixtures
- Per-fixture within-section scores with pair-level detail
- Per-fixture across-section scores with link-level detail
- Judge reasoning quoted for every pair and link

---

## Spec Revisions

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-02-05 | Initial draft — within + across section evals |
| 1.0 | 2026-02-05 | Implementation complete — all 12 fixtures, both judges, report generation |
| 1.1 | 2026-02-05 | Form D loaded from source at runtime via `{form_d}` placeholder (not hardcoded in rubrics) |
