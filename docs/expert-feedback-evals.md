# Expert Feedback Evals

New evaluation dimensions based on expert review of a PreK sound-letter B lesson.

**Source:** Expert review of `prek_letter_b_onlevel` fixture (2026-02-20)

---

## New Evals

### P0 — High Priority

These address the biggest quality gaps. Wrong standards cascade into everything else, missing activity names make lessons generic, and missing child responses force teachers to improvise.

#### 1. `grade_standards`

> Expert feedback #1, #2: "Standards were not PreK" / "Lesson is not developmentally appropriate for PreK"

| Field | Value |
|-------|-------|
| **What it checks** | Standards match the grade level. PreK must use GELDS 48-60 month indicators (e.g., CLL7.4a, CLL9.4d, PDM6.4a). K and 1st must use Georgia Standards of Excellence (ELAGSE). Activities and language are developmentally appropriate for the grade. |
| **Form dependency** | None (needs a grade-standards reference embedded in rubric) |
| **Scoring unit** | Checklist items |
| **Score formula** | `correct_items / total_items * 100` |
| **Checklist items** | (1) Correct standards system for grade, (2) Standards are real/valid codes, (3) Vocabulary is age-appropriate, (4) Motor expectations match grade, (5) Activity complexity matches grade |
| **Fixture params used** | `grade` |

#### 2. `activity_naming`

> Expert feedback #4, #5: "It did not state the activities and provide a link to a summary" / "It does not include an activity in the review section"

| Field | Value |
|-------|-------|
| **What it checks** | Each lesson section names specific Form D activities (e.g., "Sound Spark", "Magic Finger Write", "Sound-Letter Hunt") rather than generic descriptions. Materials section lists the named activities with brief summaries. Review & Connect section has a named activity. |
| **Form dependency** | Form D |
| **Scoring unit** | Sections |
| **Score formula** | `sections_with_named_activity / total_sections * 100` |
| **Per-section check** | (1) Named Form D activity present, (2) Activity name matches Form D repertoire, (3) Materials section references the activity |
| **Fixture params used** | `student_level` (determines low/middle/high activity tier) |

#### 3. `child_response_coverage`

> Expert feedback #9: "There are instances of no child response when there should be. Child response can be both verbal and what they are doing."

| Field | Value |
|-------|-------|
| **What it checks** | Every teacher prompt, question, or directed activity has a specific child response. Responses must include both **verbal** (what children say) AND **action** (what children physically do) where appropriate. No bare "(Children respond)" or "(Children do as instructed)". |
| **Form dependency** | None |
| **Scoring unit** | Interaction points |
| **Score formula** | `specific_responses / total_interaction_points * 100` |
| **Per-response check** | (1) Response is specific (not generic), (2) Verbal component present where expected, (3) Action/motor component present where expected |
| **Fixture params used** | None |

---

### P1 — Medium Priority

Important but more targeted. These catch specific pedagogical rules that matter most for PreK but affect all grade levels.

#### 4. `letter_case`

> Expert feedback #8: "Should only provide instruction for lowercase letters (provide the hint as to why), but can link to include uppercase if the teacher wants."

| Field | Value |
|-------|-------|
| **What it checks** | PreK lessons focus on lowercase letter formation only. Uppercase is optional and presented as a teacher-choice extension, not the primary instruction. K and 1st grade lessons teach both cases. |
| **Form dependency** | None |
| **Scoring unit** | Checklist items |
| **Score formula** | `correct_items / total_items * 100` |
| **Checklist items (PreK)** | (1) Primary instruction is lowercase, (2) Uppercase is optional/linked not mandatory, (3) Guided Practice focuses on lowercase, (4) Application uses lowercase |
| **Checklist items (K/1st)** | (1) Both cases are taught, (2) Both cases appear in Guided Practice |
| **Fixture params used** | `grade` |

#### 5. `verbal_cue_age`

> Expert feedback #10: "Sequence of stroke should be kid friendly not literal (e.g., straight line down, put a bubble on it)"

| Field | Value |
|-------|-------|
| **What it checks** | Stroke verbal cues use child-friendly, metaphorical language (e.g., "straight line down, put a bubble on it") rather than literal/technical terms. Cues should be consistent with Form F but adapted for the developmental register of the grade. |
| **Form dependency** | Form F (verbal cues reference) |
| **Scoring unit** | Cue instances |
| **Score formula** | `kid_friendly_cues / total_cues * 100` |
| **Per-cue check** | (1) Uses concrete/visual metaphors, (2) Avoids technical jargon, (3) Consistent across uppercase and lowercase, (4) Matches Form F where applicable |
| **Fixture params used** | `letter`, `grade` |

#### 6. `objective_alignment`

> Expert feedback #3: "Objectives did not match the standards and did not indicate what children would actually demonstrate within the activities"

| Field | Value |
|-------|-------|
| **What it checks** | Each listed objective (a) traces back to a listed standard, and (b) describes a specific, observable behavior that children actually perform in one of the scripted activities. Objectives should be testable, not aspirational. |
| **Form dependency** | None |
| **Scoring unit** | Objectives |
| **Score formula** | `aligned_objectives / total_objectives * 100` |
| **Per-objective check** | (1) Maps to a listed standard, (2) Describes observable child behavior, (3) Matches an activity in the scripted lesson |
| **Fixture params used** | `grade` |

---

### P2 — Existing Eval Recalibration

These scored well (100%) but the expert disagrees. The rubrics may be too lenient.

#### 7. Tighten `verbatim` rubric

> Expert feedback #6: "It does not state the explanation of each section"

| Field | Value |
|-------|-------|
| **Current score** | 100% (5/5 sections) |
| **Issue** | Eval checks that [Explanation] text matches Form B, and it passes. Expert says explanations are missing. Possible causes: (a) explanations exist but aren't clearly labeled/formatted in output, (b) rubric is too lenient on formatting, (c) expert is applying a different standard for "stating" the explanation. |
| **Action** | Investigate rubric. Add checks for explanation visibility/formatting, not just content match. |

#### 8. Tighten `within` rubric

> Expert feedback #7: "The sequencing within the sections are out of order"

| Field | Value |
|-------|-------|
| **Current score** | 100% (11/11 pairs) |
| **Issue** | Eval judges activity ordering within sections and passes. Expert says ordering is wrong. Possible causes: (a) judge is too generous with "valid non-escalation patterns", (b) rubric allows too many exceptions, (c) expert applies stricter pedagogical sequencing rules. |
| **Action** | Investigate rubric exemption clauses. Compare expert's expected ordering against judge's reasoning. May need stricter escalation requirements. |

---

### Not Evaluable as Fixture

#### 9. Difficulty adjustment (multi-turn)

> Expert feedback #11: "I tried asking the AI to lessen the level of difficulty and it did not do so according to the rubric guide"

| Field | Value |
|-------|-------|
| **Issue** | This tests multi-turn conversational behavior: user requests a modification, agent should re-generate with lower-difficulty Form D activities. |
| **Why it's hard** | Fixtures are single-shot lesson outputs. This requires a live conversation eval that sends a follow-up message and checks the re-generated lesson. |
| **Possible approach** | Create a separate `conversation_eval` script that runs the agent with a 2-turn sequence: (1) generate lesson, (2) "make it easier for struggling students" → check that activities shift to lower Form D tier. |

---

## Summary

| # | Eval | Priority | Type | Expert Feedback |
|---|------|----------|------|-----------------|
| 1 | `grade_standards` | P0 | New | #1, #2 |
| 2 | `activity_naming` | P0 | New | #4, #5 |
| 3 | `child_response_coverage` | P0 | New | #9 |
| 4 | `letter_case` | P1 | New | #8 |
| 5 | `verbal_cue_age` | P1 | New | #10 |
| 6 | `objective_alignment` | P1 | New | #3 |
| 7 | `verbatim` (tighten) | P2 | Recalibrate | #6 |
| 8 | `within` (tighten) | P2 | Recalibrate | #7 |
| 9 | Difficulty adjustment | P2 | New script | #11 |
