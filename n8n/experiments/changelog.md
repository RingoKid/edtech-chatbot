# n8n Lesson Generator - Experiment Log

This file tracks changes to the n8n lesson generator workflow and their outcomes.

## How to Use

After each workflow change:
1. Export workflow from n8n (Download → JSON)
2. Save as `workflows/lesson-generator-v0X.json`
3. Add entry below with hypothesis, config, and observations
4. Save sample output to `outputs/v0X-{grade}-{letter}.md`
5. Git commit

---

## v01 - 2026-01-11 - Baseline

**Hypothesis:** Basic prompt with all forms (B, C, D, F) can generate acceptable lessons

**Configuration:**
- Model: GPT-4o
- Temperature: 0.7
- Forms included: B, C, D, F (full content, no filtering)
- Prompt structure: System role + Forms + User input + Instructions

**Observations:**
- [x] All required sections present (Standards, Objectives, Materials, 5 lesson parts)
- [x] Verbatim explanations included correctly (4/5 exact, Guided Practice slightly shortened)
- [x] Correct verbal cues for target letter ("Little line across. Slant down the stairs. Little line across")
- [x] Appropriate activities selected (Sound Sparks, Sound Hunt, Magic Finger Write, Trace & Say)
- [x] Markers used correctly:
  - [x] `[Explanation: ...]` blocks
  - [x] `#Teacher Script:`
  - [x] `(Children...)` responses
  - [x] `{Teacher...}` actions
  - [x] `+Gesture:` for phoneme
  - [x] `##Sequence Verbal Cues`
  - [x] `*Adaptation:` at end
- Token usage (input): ~6,000 (estimated)
- Token usage (output): ~2,500 (9,503 chars)
- Generation time: ~16 seconds

**Sample Output:** `outputs/v01-prek-z.md`

**Notes:**
- Switched from n8n OpenAI node to HTTP Request node due to LangChain node not passing messages correctly
- API-based workflow management required (CLI lacks update/delete operations)
- Output quality matches Form C example closely
- Minor issue: Guided Practice explanation slightly shortened ("The purpose is to give" vs "The purpose of this part of the lesson is to give")

**Technical Notes:**
- Node type: `n8n-nodes-base.httpRequest` (not `n8n-nodes-base.openAi`)
- Response path: `$json.choices[0].message.content`
- Expression syntax: `$('Build Prompt').item.json.systemPrompt` for explicit node reference

---

<!-- Template for future versions

## v0X - YYYY-MM-DD - [Brief Description]

**Hypothesis:** [What you expect this change to improve]

**Changes from v0X-1:**
- [List specific changes]

**Configuration:**
- Model:
- Temperature:
- Forms included:
- Other settings:

**Observations:**
- [ ] [Checklist items]
- Token usage:
- Generation time:

**Comparison to previous:**
- Better:
- Worse:
- Same:

**Sample Output:** `outputs/v0X-{grade}-{letter}.md`

**Decision:** [Keep / Revert / Iterate]

-->
