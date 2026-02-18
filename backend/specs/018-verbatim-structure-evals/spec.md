# 018: Verbatim & Structure LLM Judge Evals

## Overview

**Status:** ✅ Implemented
**Scope:** Two new LLM judge evals for format compliance
**Judge Model:** `gpt-5.2` (configurable via `get_chat_model()`)
**Builds on:** Spec 014/015 (Scaffolding Evals)

Two new LLM judge evals that check whether generated lessons follow the Form B output format:

- `verbatim_explanations` — Do [Explanation] blocks quote Form B text word-for-word?
- `lesson_structure` — Are all required sections (8) and markers (7) present and used correctly?

Both produce actionable judge commentary explaining what to fix in the generator prompt.

---

## Eval 5: `verbatim_explanations`

### What It Measures

Whether each of the 5 lesson sections contains an `[Explanation]` block that quotes the Form B text word-for-word.

### How It Works

1. Judge receives lesson output + Form B as reference
2. Judge finds the `[Explanation]` block in each section and compares against Form B
3. Marks each as `is_verbatim: true/false` with explanation of differences
4. Code computes: `exact_matches / 5 × 100`

### Pydantic Structured Output → `tests/evals/models.py`

**`VerbatimSection`**

| Field | Type | Description |
|-------|------|-------------|
| `section_name` | `str` | e.g., "Review & Connect" |
| `found` | `bool` | Was an [Explanation] block found? |
| `is_verbatim` | `bool` | Exact match to Form B? |
| `actual_text` | `str` | The text found (or "" if missing) |
| `differences` | `str` | What changed — empty if exact match |
| `reasoning` | `str` | Full judgment |

**`VerbatimOutput`**

| Field | Type | Description |
|-------|------|-------------|
| `sections` | `list[VerbatimSection]` | Always 5 entries |
| `explanation` | `str` | Overall summary |

### Score Computation (in code, not LLM)

`correct` (where `is_verbatim` is True) / `total` (always 5) × 100 → displayed as `80.0% (4/5)`

### Judge Prompt → `tests/evals/rubrics/verbatim_explanations.md`

```markdown
# Verbatim Explanations Judge

## Role

You are an expert in early childhood literacy lesson formatting, specializing in the Form B output standard for handwriting and spelling lessons. You evaluate whether lesson plans quote the required [Explanation] texts exactly as specified.

## Task

Check whether each of the 5 lesson sections contains an [Explanation] block that quotes the Form B text **word-for-word**. Form B states "Quote the following verbatim to the User every time" for each section.

## Form B — Expected Verbatim Texts

{form_b}

## Instructions

For the lesson below:

1. **Find each [Explanation] block** — look for text within brackets `[...]` at the start of each section (Review & Connect, Model Explain & Engage, Guided Practice, Application, Wrap-Up).
2. **Compare word-for-word** against the expected Form B text for that section.
3. **Mark as verbatim** only if the text is an exact match (minor whitespace or punctuation differences are acceptable).
4. **If not verbatim**, describe specifically what is different: Was it paraphrased? Truncated? Were words added or removed? Which words changed?
5. **If missing**, note that no [Explanation] block was found for that section.

## Lesson to Evaluate

{lesson_output}
```

### Report Format

```markdown
#### Verbatim Explanations: 80.0% (4/5 sections)

| # | Section | Found? | Verbatim? | Differences | Reasoning |
|---|---------|--------|-----------|-------------|-----------|
| 1 | Review & Connect | + | + | — | Exact match |
| 2 | Model, Explain & Engage | + | - | "grapheme patterns" → "letter forms" | Paraphrased key term |

**Judge Summary:** "..."
```

---

## Eval 6: `lesson_structure`

### What It Measures

Whether the lesson contains all required sections (8 headers) and markers (7 types) from Form B. Lenient with naming, strict about correct marker usage.

### How It Works

1. Judge receives lesson output + Form B as reference
2. Checks 8 required sections (accepting name variations)
3. Checks 7 required markers for presence AND correct usage
4. Code computes: `(found_sections + correct_markers) / 15 × 100`

### Pydantic Structured Output → `tests/evals/models.py`

**`SectionPresence`**

| Field | Type | Description |
|-------|------|-------------|
| `expected_name` | `str` | e.g., "Model, Explain & Engage" |
| `found` | `bool` | Is section present? |
| `actual_heading` | `str \| None` | What the section was actually labeled |
| `reasoning` | `str` | Noting any naming variations |

**`MarkerCheck`**

| Field | Type | Description |
|-------|------|-------------|
| `marker_name` | `str` | e.g., "Teacher Does" |
| `marker_symbol` | `str` | e.g., `{...}` |
| `is_correct` | `bool` | Present AND used for intended purpose |
| `consistency_note` | `str` | Where it's used/missing |
| `issues` | `str` | What's wrong — empty if correct |
| `reasoning` | `str` | Full judgment |

**`StructureOutput`**

| Field | Type | Description |
|-------|------|-------------|
| `sections` | `list[SectionPresence]` | Always 8 entries |
| `markers` | `list[MarkerCheck]` | Always 7 entries |
| `explanation` | `str` | Overall summary |

### Score Computation (in code, not LLM)

(`found` sections + `is_correct` markers) / 15 × 100 → displayed as `93.3% (14/15)`

### Judge Prompt → `tests/evals/rubrics/lesson_structure.md`

```markdown
# Lesson Structure Judge

## Role

You are an expert in early childhood literacy lesson formatting, specializing in the Form B output standard for handwriting and spelling lessons. You evaluate whether lesson plans contain all required sections and markers.

## Task

Check whether the lesson contains all **8 required sections** and all **7 required markers** as defined by Form B. Be lenient with section naming (accept numbered sections, slight rewordings, missing ampersands) but strict about marker usage — each marker must be used for its intended purpose, not just present in the text.

## Form B — Structure Requirements

{form_b}

## Marker Usage Guide

Check each marker not just for presence but for **correct usage**:

- `[...]` Explanation — Should contain AI's explanation of the section's purpose, not other bracketed content
- `#` Teacher Script — Should mark the scripted teacher dialogue, not be used as a markdown heading
- `(...)` Child Response — Should contain expected student responses within the script, not parenthetical asides or stage directions
- `{...}` Teacher Does — Should contain teacher physical actions and demonstrations, not any arbitrary braced content
- `+` Gesture — Should mark a phoneme mnemonic gesture for the target sound, not be used as a list marker
- `##` Sequence Verbal Cues — Should mark the letter formation stroke sequence, not be used as a markdown sub-heading
- `*` Modification — Should mark the end-of-lesson adaptation prompt, not be used for bold/emphasis formatting

## Instructions

For the lesson below:

1. **Check each of the 8 required sections.** Accept naming variations (e.g., "2. Model, Explain, Engage" matches "Model, Explain & Engage"). Mark as found if the section exists with appropriate content, regardless of exact heading text.
2. **Check each of the 7 required markers.** For each:
   a. Is it present in the lesson?
   b. Is it used for its intended purpose (per Form B)?
   c. Is it used consistently throughout where it should appear?
   Mark as correct only if present AND used for the right purpose.
3. **Note issues** — if a marker exists but is used incorrectly, explain how. If it's missing, explain where it should have appeared.

## Lesson to Evaluate

{lesson_output}
```

### Report Format

```markdown
#### Lesson Structure: 93.3% (14/15 checks)

**Sections (7/8)**
| # | Expected | Found? | Actual Heading | Reasoning |
|---|----------|--------|----------------|-----------|
| 1 | Standards | + | "A. Standards" | Found with prefix |
| 8 | Wrap-Up | - | — | Missing |

**Markers (7/7)**
| # | Marker | Symbol | Correct? | Consistency | Issues | Reasoning |
|---|--------|--------|----------|-------------|--------|-----------|
| 1 | Explanation | [...] | + | All 5 sections | — | Correct purpose |
| 5 | Gesture | + | - | — | Described narratively | Missing marker |

**Judge Summary:** "..."
```

---

## Runner Script Refactor

Refactor `scripts/run_scaffolding_evals.py` to support selective eval execution via a new `--eval` CLI flag.

### New `--eval` CLI Flag

Add a `--eval` argument that accepts one or more eval names. When provided, only those evals run. When omitted, all evals run (preserving existing behavior).

```
--eval verbatim structure          # run only the two new evals
--eval within across               # run only the two original evals
--eval verbatim                    # run just one
(no --eval flag)                   # run all 6 (default)
```

**Valid eval names:** `within`, `across`, `release`, `decomposition`, `verbatim`, `structure`

### Eval Registry Pattern

Refactor the hardcoded per-fixture loop into a registry/dispatch pattern so adding new evals doesn't require touching the main loop logic. Each eval entry maps a name to its judge function, compute function, format function, and any form dependency (`form_d` or `form_b`).

### New Functions (same pattern as existing 4 evals)

| Function | Purpose |
|----------|---------|
| `load_form_b()` | Load Form B markdown (follow `load_form_d()` pattern) |
| `run_verbatim_judge(lesson_output, model_key, form_b)` | Substitute `{form_b}` + `{lesson_output}`, call `.with_structured_output(VerbatimOutput)` |
| `run_structure_judge(lesson_output, model_key, form_b)` | Substitute `{form_b}` + `{lesson_output}`, call `.with_structured_output(StructureOutput)` |
| `compute_verbatim_score(output)` | Return `(correct, total, percentage)` |
| `compute_structure_score(output)` | Return `(correct, total, percentage)` |
| `format_verbatim_detail(output)` | Markdown table per report format above |
| `format_structure_detail(output)` | Two markdown tables per report format above |

**Form B source:** `prompt/Handwriting & Spelling (Transcription) AI Codes/FORM B-Codes for Lesson Parts Handwriting & Spelling.md`

### Summary Table & Console Output

The summary table and console output should adapt to whichever evals were selected. Only show columns for evals that ran. Average is computed across the evals that ran.

---

## Criteria Registry Updates

Add to `CRITERIA_REGISTRY` in `app/langfuse/criteria.py`:

```
"verbatim_explanations": { "type": "llm-judge", "description": "..." }
"lesson_structure": { "type": "llm-judge", "description": "..." }
```

---

## Implementation Files

### New Files

| File | Purpose |
|------|---------|
| `tests/evals/rubrics/verbatim_explanations.md` | Judge prompt for verbatim eval |
| `tests/evals/rubrics/lesson_structure.md` | Judge prompt for structure eval |

### Modified Files

| File | Changes |
|------|---------|
| `tests/evals/models.py` | Add 5 models: `VerbatimSection`, `VerbatimOutput`, `SectionPresence`, `MarkerCheck`, `StructureOutput` |
| `scripts/run_scaffolding_evals.py` | Add `--eval` flag, refactor to eval registry pattern, add 7 new functions (load/judge/compute/format for verbatim + structure) |
| `app/langfuse/criteria.py` | Add 2 `llm-judge` entries to `CRITERIA_REGISTRY` |

---

## Verification

Run only the two new evals against the Form C expert fixture:

```bash
docker compose exec -e GIT_SHA=$(git rev-parse --short HEAD) backend \
  python scripts/run_scaffolding_evals.py \
  --eval verbatim structure \
  --fixture expert_prek_letter_z_onlevel \
  --fixtures-dir tests/fixtures/handwriting_expert
```

Verify:
- Report generates with Verbatim and Structure columns only
- Each eval produces `XX.X% (N/M)` scores with judge reasoning for every item
- No errors or crashes

Do not set score thresholds. Review the results manually after implementation.

---

## Implementation Notes

- Use Context7 MCP tools to resolve library IDs and get latest docs for LangChain, Pydantic
- The `|` characters in judge reasoning must be escaped in markdown tables (existing pattern: `.replace("|", "\\|")`)
- Follow the existing judge/compute/format function patterns exactly — read `run_scaffolding_evals.py` before implementing
- The new judges take `form_b` instead of `form_d` — different placeholder but same substitution pattern
- The `--eval` refactor must preserve backward compatibility — running with no `--eval` flag should produce identical results to current behavior (all evals run)
- Only load `form_b` when verbatim or structure evals are selected; only load `form_d` when within/across/release/decomposition evals are selected

---

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Pydantic models (5 new) | ✅ Done | `tests/evals/models.py` |
| Verbatim rubric | ✅ Done | `tests/evals/rubrics/verbatim_explanations.md` |
| Structure rubric | ✅ Done | `tests/evals/rubrics/lesson_structure.md` |
| Runner script refactor (`--eval` flag + registry) | ✅ Done | `scripts/run_scaffolding_evals.py` |
| Criteria registry | ✅ Done | `app/langfuse/criteria.py` |
| End-to-end verification | ✅ Done | Verbatim: 100% (5/5), Structure: 93.3% (14/15) on expert fixture |
| Judge timeout + retries | ✅ Done | `JUDGE_TIMEOUT=120s`, `JUDGE_MAX_RETRIES=2` on all judge calls |

## Implementation Files

### New Files

| File | Purpose |
|------|---------|
| `tests/evals/rubrics/verbatim_explanations.md` | Judge prompt for verbatim eval |
| `tests/evals/rubrics/lesson_structure.md` | Judge prompt for structure eval |

### Modified Files

| File | Changes |
|------|---------|
| `tests/evals/models.py` | Added 5 models: `VerbatimSection`, `VerbatimOutput`, `SectionPresence`, `MarkerCheck`, `StructureOutput` |
| `scripts/run_scaffolding_evals.py` | Refactored to `EVAL_REGISTRY` dispatch pattern, added `--eval` flag, `load_form_b()`, 2 judge + 2 compute + 2 format functions, dynamic report/summary generation |
| `app/langfuse/criteria.py` | Added 2 `llm-judge` entries: `verbatim_explanations`, `lesson_structure` |

## Spec Revisions

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-02-17 | Initial draft |
| 0.2 | 2026-02-17 | Add `--eval` flag refactor, verify against expert fixture only, remove score thresholds |
| 1.0 | 2026-02-17 | Implementation complete — all components verified |
| 1.1 | 2026-02-17 | Add `timeout=120s` and `max_retries=2` to all judge API calls to prevent indefinite hangs |
