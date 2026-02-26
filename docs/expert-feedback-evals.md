# Expert Feedback Evals

New evaluation dimensions based on expert review of a PreK sound-letter B lesson.

**Source:** Expert review of `prek_letter_b_onlevel` fixture (2026-02-20)

---

## Dr. Farrow Clarifications (2026-02-22)

Answers from follow-up conversations about standards, grade-level differences, and notation.

### Standards System

- **Confirmed:** The old ELAGSE codes (e.g., ELAGSEKRF3a) are deprecated. Use the new systems:
  - **PreK** → GELDS 48-60 month indicators (CLL/PDM codes)
  - **K** → Georgia K-12 ELA Standards SY2025-2026 (K.F.* codes)
  - **1st** → Georgia K-12 ELA Standards SY2025-2026 (1.F.* codes)

- **PreK valid codes narrowed to 6.** Dr. Farrow specified only these GELDS codes are relevant to handwriting/spelling lessons:

  | Code | Description |
  |------|-------------|
  | CLL6.4c | Isolates the initial (beginning) sounds in words with adult guidance |
  | CLL6.4e | Segments words into syllables |
  | CLL6.4f | Manipulates and blends sounds (phonemes) with adult guidance |
  | CLL7.4a | With prompting and support, recognizes and names some upper/lowercase letters |
  | CLL8.4b | Understands that letters form words. Words are separated by spaces in print |
  | CLL9.4d | Writes some letters of the alphabet |

  The remaining 8 codes in the reference file (CLL6.4a, CLL6.4b, CLL6.4d, CLL9.4a, CLL9.4b, PDM6.4a-c) are NOT relevant to handwriting/spelling lessons.

- **K and 1st grade require at least 4 standards**, one from each of these categories:

  | Category | K codes | 1st codes |
  |----------|---------|-----------|
  | Phonemic Awareness | K.F.PA.* | 1.F.PA.* |
  | Phoneme-Grapheme Correspondence | K.F.P.1.* | 1.F.P.1.* |
  | Encoding | K.F.P.3.* | 1.F.P.3.* |
  | Handwriting | K.F.H.* | 1.F.H.* |

  **Excluded:** Decoding standards (K.F.P.2.*, 1.F.P.2.*) — these are reading standards, not handwriting/spelling.

- **Standards selection depends on lesson content.** The AI should pick codes based on what the teacher is working on, not just the grade level.

### Form C Code Replacement (Confirmed Correct)

The PreK letter Z example (Form C) originally had old Kindergarten ELAGSE codes. Replaced with GELDS codes, confirmed correct by Dr. Farrow:

| Old (ELAGSE) | New (GELDS) |
|-------------|-------------|
| ELAGSEKRF3a — Produce primary sound for each consonant | CLL6.4c — Isolates initial sounds in words |
| ELAGSEKL1a — Print upper/lowercase letters | CLL7.4a — Recognizes and names upper/lowercase letters |
| ELAGSEKL2c — Write letters for consonant/short-vowel sounds | CLL9.4d — Writes some letters of the alphabet |

### Skill Focus Question (Approved)

Dr. Farrow approved adding a new intake question: **"What skill are you focusing on?"** Currently the teacher only provides grade, letter, and student level. Adding a skill focus (e.g., isolating sounds, blending, letter formation, spelling) would help the AI select the right standards. Not yet implemented.

### Grade-Level Differences

Dr. Farrow's explanation of what changes between PreK, K, and 1st grade:

1. **Standards scope** — Different grades have different standards available. PreK has print concepts (CLL8.4b), 1st grade doesn't.

2. **Prior knowledge accumulation:**
   - **PreK:** Teaching individual sounds/letters from scratch. Guided practice = finger tracing on lines, finding top/middle/bottom.
   - **K:** Building on some prior sound knowledge.
   - **1st:** All consonant and vowel sounds already known, including corresponding graphemes. Focus shifts to handwriting fluency, spelling patterns, and cementing orthographic representations. Teacher can increase letter amount. Guided practice targets key letters/patterns kids will use to spell words in Application.

3. **Cognitive load capacity** — A 6-year-old has more working memory than a 4-year-old:
   - **PreK:** More breaking down, more scaffolds, simpler steps.
   - **1st:** Less scaffolding needed, activities can be more complex.
   - This applies between grades AND within grades by ability level.

**Pending:** Dr. Farrow offered to provide a developmental chart with concrete rules per grade level. Will integrate into the system prompt once received.

### Notation Conventions (Approved to Change)

The current notation markers (#, *, ##) use markdown characters that break formatting in the chatbot. Dr. Farrow approved finding alternatives that display cleanly. Current markers that need replacement:

| Current | Used for | Problem |
|---------|----------|---------|
| `#Teacher Script` | What the teacher says | Renders as heading |
| `##Sequence Verbal Cues` | Letter formation cues | Renders as heading |
| `*Modification` | End-of-lesson prompt | Renders as italic |

These don't break: `[Explanation]`, `(Child Response)`, `{{Teacher Does}}`, `+Gesture`

### Pending Items

- [ ] K-level example lessons with Standards and Objectives sections (Dr. Farrow sending tonight 2026-02-22)
- [ ] Complete Form C-style examples for K and 1st grade (requested)
- [ ] Developmental chart for grade-level differences (Dr. Farrow will provide, no rush)
- [ ] Implement skill focus intake question
- [ ] Replace notation conventions with markdown-safe alternatives

---

## Eval Status

| # | Eval | Priority | Status | Expert Feedback |
|---|------|----------|--------|-----------------|
| 1 | `grade_standards` | P0 | Implemented — needs recalibration | #1, #2 |
| 2 | `activity_naming` | P0 | Implemented | #4, #5 |
| 3 | `child_response_coverage` | P0 | Implemented | #9 |
| 4 | `letter_case` | P1 | Not started (standalone — considered folding into `grade_content_scope`, keeping separate) | #8 |
| 5 | `verbal_cue_age` | P1 | Not started | #10 |
| 6 | `objective_alignment` | P1 | Not started | #3 |
| 7 | `verbatim` (tighten) | P2 | Recalibrate | #6 |
| 8 | `within` (tighten) | P2 | Recalibrate | #7 |
| 9 | Difficulty adjustment | P2 | Not started (multi-turn) | #11 |
| 10 | `grade_activity_appropriateness` | P0 | Not started | Grade-level activity analysis |
| 11 | `developmental_techniques` | P1 | Not started | Grade-level activity analysis |
| 12 | `grade_content_scope` | P1 | Not started | Grade-level activity analysis |

---

## Evals Detail

### P0 — High Priority

#### 1. `grade_standards`

> Expert feedback #1, #2: "Standards were not PreK" / "Lesson is not developmentally appropriate for PreK"

| Field | Value |
|-------|-------|
| **What it checks** | Standards match the grade level. PreK must use GELDS 48-60 month indicators (only the 6 approved codes). K and 1st must use Georgia K-12 ELA Standards SY2025-2026 (K.F.* / 1.F.* codes). Activities and language are developmentally appropriate for the grade. |
| **Form dependency** | None (grade-standards reference embedded in rubric) |
| **Scoring** | Composite: 50% standards accuracy + 50% developmental appropriateness |
| **Fixture params used** | `grade` |
| **Status** | Implemented in spec 020. Rubric needs recalibration (see below). |

**Recalibration needed:**

1. **PreK valid codes too broad.** Rubric currently lists 14 GELDS codes. Must be narrowed to the 6 Dr. Farrow approved. The 8 excluded codes (CLL6.4a, CLL6.4b, CLL6.4d, CLL9.4a, CLL9.4b, PDM6.4a-c) should fail `relevant_to_handwriting`.

2. **K/1st decoding codes should be excluded.** Rubric currently lists K.F.P.2.* and 1.F.P.2.* as valid. These are reading/decoding standards and should fail `relevant_to_handwriting`.

3. **No category coverage check.** K/1st lessons must have at least 4 standards, one from each category (PA, P.1, P.3, H). Current eval only checks each standard individually — no way to detect missing categories. Options:
   - Add category coverage to the scoring function (classify valid codes by pattern, check 4 categories are present)
   - Or add a new Pydantic field for category coverage

4. **Standards selection accuracy.** Currently the eval checks if codes are valid and from the right system, but not whether the specific codes match the lesson content. Full accuracy requires knowing the target skill (pending skill focus intake question). For now, can only check system + validity + relevance.

#### 2. `activity_naming`

> Expert feedback #4, #5: "It did not state the activities and provide a link to a summary" / "It does not include an activity in the review section"

| Field | Value |
|-------|-------|
| **What it checks** | Each lesson section names specific Form D activities (e.g., "Sound Spark", "Magic Finger Write", "Sound-Letter Hunt") rather than generic descriptions. Materials section lists the named activities. |
| **Form dependency** | Form D |
| **Scoring** | Composite: 60% section naming + 40% materials coverage |
| **Fixture params used** | `student_level` (determines low/middle/high activity tier) |
| **Status** | Implemented in spec 020. |

#### 3. `child_response_coverage`

> Expert feedback #9: "There are instances of no child response when there should be. Child response can be both verbal and what they are doing."

| Field | Value |
|-------|-------|
| **What it checks** | Every teacher prompt/question/directed activity has a specific child response. Responses must include both verbal (what children say) AND action (what children do) where appropriate. No bare "(Children respond)". |
| **Form dependency** | None |
| **Scoring** | Composite: 30% presence + 30% specificity + 40% completeness |
| **Fixture params used** | None |
| **Status** | Implemented in spec 020. |

---

### P1 — Medium Priority

#### 4. `letter_case`

> Expert feedback #8: "Should only provide instruction for lowercase letters (provide the hint as to why), but can link to include uppercase if the teacher wants."

| Field | Value |
|-------|-------|
| **What it checks** | PreK lessons focus on lowercase letter formation only. Uppercase is optional extension. K and 1st teach both cases. |
| **Form dependency** | None |
| **Scoring** | Checklist: `correct_items / total_items * 100` |
| **Checklist (PreK)** | (1) Primary instruction is lowercase, (2) Uppercase is optional not mandatory, (3) Guided Practice focuses on lowercase, (4) Application uses lowercase |
| **Checklist (K/1st)** | (1) Both cases are taught, (2) Both cases appear in Guided Practice |
| **Fixture params used** | `grade` |
| **Status** | Not started. |

#### 5. `verbal_cue_age`

> Expert feedback #10: "Sequence of stroke should be kid friendly not literal (e.g., straight line down, put a bubble on it)"

| Field | Value |
|-------|-------|
| **What it checks** | Stroke verbal cues use child-friendly, metaphorical language rather than literal/technical terms. Cues should match Form F but adapted for grade level. |
| **Form dependency** | Form F (verbal cues reference) |
| **Scoring** | `kid_friendly_cues / total_cues * 100` |
| **Fixture params used** | `letter`, `grade` |
| **Status** | Not started. |

#### 6. `objective_alignment`

> Expert feedback #3: "Objectives did not match the standards and did not indicate what children would actually demonstrate within the activities"

| Field | Value |
|-------|-------|
| **What it checks** | Each objective (a) traces back to a listed standard, (b) describes observable behavior children actually perform in the lesson. |
| **Form dependency** | None |
| **Scoring** | `aligned_objectives / total_objectives * 100` |
| **Fixture params used** | `grade` |
| **Status** | Not started. |

---

### P2 — Existing Eval Recalibration

#### 7. Tighten `verbatim` rubric

> Expert feedback #6: "It does not state the explanation of each section"

| Field | Value |
|-------|-------|
| **Current score** | 100% (5/5 sections) |
| **Issue** | Eval passes but expert says explanations are missing. Possible: explanations exist but aren't clearly labeled/formatted, or rubric is too lenient on formatting. |
| **Action** | Add checks for explanation visibility/formatting, not just content match. |

#### 8. Tighten `within` rubric

> Expert feedback #7: "The sequencing within the sections are out of order"

| Field | Value |
|-------|-------|
| **Current score** | 100% (11/11 pairs) |
| **Issue** | Eval passes but expert says ordering is wrong. Judge may be too generous with exceptions. |
| **Action** | Investigate rubric exemption clauses. Compare expert's expected ordering against judge's reasoning. |

---

### Not Evaluable as Fixture

#### 9. Difficulty adjustment (multi-turn)

> Expert feedback #11: "I tried asking the AI to lessen the level of difficulty and it did not do so according to the rubric guide"

| Field | Value |
|-------|-------|
| **Issue** | Multi-turn conversational behavior: user requests a modification, agent should re-generate with lower-difficulty Form D activities. |
| **Why it's hard** | Fixtures are single-shot. Requires live conversation eval. |
| **Possible approach** | Separate script with 2-turn sequence: (1) generate lesson, (2) "make it easier" → check activities shift to lower Form D tier. |
| **Status** | Not started. |

---

### P0 — Grade-Level Activity Evals

#### 10. `grade_activity_appropriateness`

> Grade-level analysis: Activities in the lesson must be appropriate for the target grade.

| Field | Value |
|-------|-------|
| **What it checks** | Hybrid rule-based + LLM judge. **Rule-based:** No banned activities for the grade (e.g., Magic Finger Write banned for 1st, Disappearing Letter banned for PreK). Uses allowlist/blocklist per grade. **LLM judge:** For cross-grade activities (Sound Hunt, Sound-Letter Hunt), checks delivery matches the grade (e.g., Sound Hunt = beginning-sounds-only for PreK, beginning+ending for K, medial vowels for 1st). |
| **Form dependency** | Form D (activity menu) |
| **Scoring** | Composite: rule-based blocklist check + LLM judge delivery check |
| **Fixture params used** | `grade`, `student_level` |
| **Status** | Not started. |

---

### P1 — Grade-Level Technique & Content Evals

#### 11. `developmental_techniques`

> Grade-level analysis: Teaching methods (not activity-specific) must be appropriate for the grade.

| Field | Value |
|-------|-------|
| **What it checks** | LLM judge. 6 technique checks, each pass/fail: (1) Directionality instruction — required PreK, not for 1st. (2) Mouth/articulation placement — expected PreK, not for 1st. (3) Choral repetition intensity. (4) Pencil grip instruction. (5) Teacher modeling ratio — heavy PreK, light 1st. (6) Line identification (top/middle/bottom). |
| **Form dependency** | None |
| **Scoring** | `appropriate_count / 6 * 100` |
| **Fixture params used** | `grade` |
| **Status** | Not started. |

#### 12. `grade_content_scope`

> Grade-level analysis: Content complexity and scope must match the target grade.

| Field | Value |
|-------|-------|
| **What it checks** | LLM judge. 5-6 content checks: (1) Sound isolation type — beginning only PreK, beginning+ending K, medial 1st. (2) Spelling scope — single letter PreK, CVC K, CVCe 1st. (3) Prior knowledge assumptions — teach from scratch PreK, all sounds known 1st. (4) Review activity complexity. (5) Phonemic task type. |
| **Form dependency** | None |
| **Scoring** | `appropriate_count / total_checks * 100` |
| **Fixture params used** | `grade` |
| **Status** | Not started. |
