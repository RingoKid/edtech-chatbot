# Language Construction TODO

<!-- Split from main TODO on 2026-04-19 for focused LC tracking. -->
<!-- Managed by /dev sub-skills. Grouped by phase, checkbox style. -->

## Section-by-section comparison (cycle 3 walkthrough)

### Why we're doing this

Comparing the v3 generated lesson plan against the reference example, section by section, to:

1. **Understand each section** — what it's doing pedagogically and how it's doing it
2. **Map output to prompt** — for each section, pinpoint the exact system-prompt lines/rules that drive its content, structure, and styling
3. **Collect prompt-improvement TODOs** — every divergence that isn't cosmetic feeds into a punch list for later prompt edits
4. **Decide per-section whether to add an eval** — if a behavior is load-bearing AND testable from output alone, capture it as an eval candidate
5. **Build a complete mental model** of the prompt → output relationship so future prompt edits are informed, not random
6. **Evaluate whether this walkthrough methodology itself should become a reusable sub-skill** (e.g. `/dev lc-compare`) once we see how it plays out across all 10 sections

This is **not** a verbatim-match exercise. v3 generated output and reference are both legitimate lessons — we're looking at how well the prompt encodes the *shape* of a good lesson, not whether the AI produced identical text.

### Files in play (cycle 3)

| Role | Path |
|---|---|
| System prompt source | `backend/scripts/prototype_lc_generator.py` (template lines 75–167; rules 1–13 at lines 117–151) |
| Generated output (v3) | `backend/scripts/prototype-lc-outputs/lc_lesson_K_2026-04-20_025048.md` (385 lines) |
| Reference (comparison target) | `backend/prompt/reference_materials/language_construction/prompt-ready/lesson-plan-k-example.md` (385 lines) |
| Standards fact-check source | `backend/prompt/reference_materials/language-construction-standards.md` |
| Other reference materials injected | Form I (lesson structure), Form M (genre), Form R (sentence structure), Form K (scaffolded activities), Form E (best practices) — all under `backend/prompt/reference_materials/language_construction/prompt-ready/` |

**Cycle 3 inputs** (in `INPUTS` dict of `prototype_lc_generator.py`): grade K / informational / weather & temperature / vocabulary [weather, temperature, thermometer, chilly, freezing] / sentence structure "Be-verbs" / previously learned action verbs + -y adjective rule / ability level "on target". **Identical to the reference example inputs** — any divergence in output reflects prompt design, not input drift.

### How to run a section comparison (resumable method)

For each section below, follow these steps:

1. **Pull the section from all three sources**
   - Read the section from v3 output (use `Read` with `offset`/`limit`)
   - Read the same section from the reference
   - Locate the prompt lines that govern the section in `prototype_lc_generator.py`:
     - Output structure clauses: lines 91–105 (sections A/B/C/D, subsection order)
     - Component markers: lines 107–114 (emoji markers and when to use them)
     - Rules 1–13: lines 117–151 (mapped below)

2. **Describe what the section is doing** — one sentence on pedagogical purpose (from Form I for D subsections).

3. **Map prompt-to-output**
   - Which template line numbers specify the structure?
   - Which numbered rules govern the content? (e.g. Rule 6 = worked + non-examples, Rule 8 = corrective feedback, Rule 2 = Form K activity names)
   - Which reference material is being used as ground truth? (Form I for explanations, Form K for activities, Form R for sentence structures, Form M for genre, standards file for codes)

4. **Compare verdict-style**
   - ✅ **Matching** — same structure, content, style
   - ⚠️ **Cosmetic drift** — different styling but pedagogically equivalent (e.g. bold vs plain labels, bullet vs paragraph)
   - 🔴 **Real gap** — missing rule application, content fabrication, or pedagogical regression

5. **Collect TODOs** — any actionable prompt improvement goes into "TODO list for prompt updates" below, tagged with the section that surfaced it.

6. **Eval decision** — apply the criteria below. If yes, add to "Eval candidates."

### Rule-to-section cheat sheet

| Section | Primary prompt drivers |
|---|---|
| Title + Input | lines 104–105 (H2 title + byline + Input list format) |
| A. Standards | line 94 + Rule 10 (line 144) + standards reference block |
| B. Objectives | line 95 ("listed in order of difficulty") |
| C. Materials | line 96 ("concrete list") |
| D.1 Review & Connect | Rule 1 (Form I purpose quote), Rule 9 (bridge from previously learned), Rule 11 (turn-taking), Rule 2 (Form K activity names), Rule 5 (example bank) |
| D.2 Model, Explain & Engage | Rule 1, Rule 6 (2 worked + 2 non-examples), Rule 7 (genre integration), Rule 8 (corrective feedback), Rule 2, Rule 5 |
| D.3 Guided Practice | Rule 1, Rule 2, Rule 3 (activity-level matching), Rule 4 (verbatim script), Rule 5, Rule 8, Rule 11 |
| D.4 Application | Rule 1, Rule 3 (high-level activity for on-target), Rule 5, Rule 8 |
| D.5 Wrap-Up | Rule 1, Rule 11, Rule 12 (warmth, not clinical) |
| Adaptation footer | Rule 13 (verbatim closing line) |

### Eval decision criteria

Add to "Eval candidates" if **all three** hold:

- **Output-testable** — behavior can be verified from the markdown alone (no graph state, no human judgment)
- **Class of error, not instance** — the test catches a family of regressions, not just today's bug
- **Load-bearing** — silent failure would ship a materially worse lesson to teachers

Examples that qualify: "every standards code exists in the standards file," "every activity name matches a heading in Form K," "every section opens with 💡 + verbatim Form I quote."

Examples that don't qualify: "bolding on Input labels" (cosmetic), "title uses em-dash" (stylistic).

### Section checklist

- [x] 0. Title + Input block — done 2026-04-19
- [x] A. Standards — done 2026-04-19 (surfaced K.L.GC.2.c miscoding, fixed)
- [ ] B. Objectives
- [ ] C. Materials
- [ ] D.1 Review & Connect
- [ ] D.2 Model, Explain & Engage
- [ ] D.3 Guided Practice
- [ ] D.4 Application
- [ ] D.5 Wrap-Up
- [ ] Adaptation footer

### Findings log

#### Section 0 — Title + Input block ✅ (2026-04-19)

**Prompt driver:** lines 104–105 of template.

**What matched:** Grade, genre, unit focus, vocabulary (5 words), sentence structure focus ("Be-verbs"), previously learned phrasing, ability level — all input fields echoed correctly.

**Cosmetic drift:**
- v3 expands structure verbatim into title (`Be-verbs (Weather and temperature)`); reference condenses (`Be-Verbs (Weather/Temperature)`). Caused by template literal `## Lesson Plan {grade}: Sentence Structure — {sentence_structure_focus} ({unit_focus})`.
- v3 bolds every Input label (`**Grade:**`); reference uses plain labels. Caused by the prompt template itself bolding the field names at lines 83–89 — model mirrors the prompt's own styling.
- v3 orders Input list Grade → Genre → Unit Focus → ... (matches template order); reference leads with Unit focus.
- v3 ability level is lowercase "on target"; reference is "On target." (v3 echoed `INPUTS` dict value verbatim).

**Real gaps:** none.

**TODOs surfaced:** none (all cosmetic).

**Eval candidate:** maybe — "every lesson starts with `## Lesson Plan {grade}:` H2 and includes a labeled `**Input:**` block." Low ROI; format is enforced by the prompt's explicit template so regression is unlikely unless the template itself changes.

#### Section A — Standards ✅ (2026-04-19)

**Prompt drivers:** line 94 (structure clause) + Rule 10 (line 144, priority order + "do not fabricate") + standards reference block injected at top of reference materials.

**v3 produced:**
```
- K.L.GC.2.a — Recognize that conventional sentences always include a subject and a predicate.
- K.L.V.1.b — Use grade-level general, academic, and specialized vocabulary...
- K.P.AC.2.c — Make decisions about sentence structure and syntax...
```

**Reference produced (post-fix):**
```
K.P.AC.2.c — Make decisions about sentence structure and syntax...
K.L.GC.2.a — Recognize that conventional sentences always include a subject and a predicate.
K.L.GC.2.b — With adult support, use simple sentences to express complete thoughts in written texts.
```

**What matched / exceeded:**
- v3 selected 3 codes within the prompt's 1–3 range ✅
- All 3 codes exist verbatim in `language-construction-standards.md` ✅
- v3 followed Rule 10's priority order (GC → V → AC); **reference violates it** (AC first). AI out-aligned the human reference on stated priority.

**What we caught:** reference's original `K.L.GC.2.c` description was miscoded — it belonged to `K.L.GC.2.b`. Fixed in both copies this session.

**Cosmetic drift:**
- v3 uses bulleted list with `**bold code**`; reference uses plain-paragraph format. Driven by the prompt template's bullet styling, not by a rule.

**Real gaps:** none in v3. The miscoding was in the human-authored reference.

**TODOs surfaced:**
- [ ] Decide whether Rule 10's stated priority (GC → V → AC) should stand, given the reference violates it. Check with Dr. Farrow if the AC-first ordering in reference was intentional. (from Section A)

**Eval candidate: YES — HIGH VALUE**
- [ ] **Standards fidelity eval** — for any generated LC lesson, assert (1) every code in `### A. Standards` exists in `language-construction-standards.md`, (2) the description matches the standards file verbatim, (3) count is within 1–3. Would catch hallucinations AND reference miscodings. Tentative file: `backend/tests/evals/lc/test_standards_fidelity.py`.

### TODO list for prompt updates (surfaced from walkthrough)

Running list. Each item tagged with the section that surfaced it.

- [ ] Decide whether Rule 10's priority order (GC → V → AC) should stand given reference violates it — check with Dr. Farrow (from Section A)

### Eval candidates (triaged during walkthrough)

Running list. Promote to real eval files once Phase 3 graph integration begins.

- [ ] Standards fidelity eval — codes exist in standards file + descriptions match verbatim + count 1–3 (from Section A)

### Sub-skill consideration

Deferred decision. If the section-walkthrough pattern holds across all 10 sections (especially D.1–D.5 which are content-heavy), consider packaging as `/dev lc-compare <section>` with these capabilities:

- Auto-loads the three files (v3 output, reference, prompt script)
- Pre-locates the section text in all three using markdown heading regex
- Pre-populates the rule-to-section cheat sheet and prompts for findings
- Appends findings to `TODO-LC.md` under the right subsection
- Bumps the section checklist

Decide after finishing all 10 sections; premature sub-skill creation is overhead if the method keeps changing.

---

## Prototype cycle findings (2026-04-19)

- [x] **Fix K.L.GC.2.c miscoding in LC example lessons** — Reference `lesson-plan-k-example.md` listed `K.L.GC.2.c — Use simple sentences to express complete thoughts in written texts.`; per curated `language-construction-standards.md`, that description actually belongs to `K.L.GC.2.b` ("With adult support, use simple sentences..."). Fixed in both `prompt-ready/lesson-plan-k-example.md` and the comment-bearing duplicate `language_construction/lesson-plan-k-example.md`. Discovered via cycle 3 of `prototype_lc_generator.py`. (2026-04-19)
- [ ] **Flag K.L.GC.2.c → K.L.GC.2.b correction to Dr. Farrow** — In the Phase 2 review email, mention that the standards code in `lesson-plan-k-example.md` was realigned to `K.L.GC.2.b` per the SY2025-2026 GSE source. Confirm she agrees with the change. (2026-04-19)

## Rollout (Dr. Farrow, 2026-04-15)

Ordered by execution path (prototype-first approach). Core path: prep reference materials → build standalone prototype → Dr. Farrow review → integrate. Secondary items (more FORM K activities, extra samples, PreK/1st standards) unblock later phases or improve iteration quality.

**Original commitment (superseded):**

- [ ] **Ship language construction lesson generator by 2026-04-17 EOD** — Original commitment to Dr. Farrow. Superseded 2026-04-17 by prototype-first plan (build standalone → send for review → integrate after approval). Keep here for context; re-word or close once new timeline is agreed with Dr. Farrow. (email thread, 2026-04-15)

**Core path (do in this order):**

- [x] **1. Update language construction standards to new code format (K grade)** — Built `backend/prompt/reference_materials/language-construction-standards.md` with curated K.L.GC, K.L.V, and K.P.AC.2.c codes (narrow filter: syntax + grammar + vocabulary only). Fixed miscoded `K.P.ST.2.c` → `K.P.AC.2.c` in `lesson-plan-k-example.md` along the way. (2026-04-17)
- [x] **2. Convert LC example lessons to emoji notation** — Both example lessons (`form-j-example-lesson.md`, `lesson-plan-k-example.md`) still use Form I's original notation: `[Explanation:...]`, `#Teacher Script:`, `(child response)`, `{Teacher Does}`, `*Modification`, `^Modified script`. Handwriting examples were migrated to emoji markers: 💡 **Explanation**, 🗣️ **Teacher**, 💬 **Child Response**, 👉 **Teacher Does**, 🔄 **Adaptation**. Convert both LC samples to the same convention and update Form I's component legend to match so references and generator prompt stay aligned. Blocks the prototype — prompt should teach the generator emoji output from day one. (scope 2026-04-17)
- [ ] **3. Phase 1: build LC generator prototype (standalone)** — Create `backend/scripts/prototype_lc_generator.py` with hardcoded inputs (K / informational / weather vocab / be-verbs / on-level). Load LC reference materials (Forms I, E, K, M, R + emoji'd examples) + K standards file. Call `gpt-5.4`, write output to file. No graph wiring. Iterate prompt manually against `lesson-plan-k-example.md` as structural-fidelity target (not verbatim). Cross-check against Form J inputs (sea creatures, be-verbs) to catch overfitting. Blocked on: task 2. (scope 2026-04-17)
- [ ] **4. Phase 2: send LC prototype output to Dr. Farrow for review** — Package the best prototype output + system prompt for review. Deliver via usual Dropbox/email path. Blocks Phase 3 until approved. Blocked on: task 3. (scope 2026-04-17)
- [ ] **5. Phase 3: integrate LC generator into graph** — After Dr. Farrow approves: build `backend/app/graph/agents/language_construction_generator.py` + `language_construction_generator_node` in `graph.py`. Replace `vocabulary_generator_placeholder` wiring. Thread modification flow via `lesson_markdown` detection. Connect image pipeline (`image_assembly` → `image_director`). Update `entry_router` for LC modification re-entry. Smoke test + deploy. Blocked on: task 4 approval. (scope 2026-04-17)

**Iteration-quality helpers (run in parallel with core path, each gates on Dr. Farrow's revision turnaround):**

- [ ] **6. Draft additional FORM K activities via ChatGPT** — FORM K alone may not cover the activity range needed. Scope strictly to the 5 sentence-structure verbs: identify, build, imitate, expand, combine. NO mixing with handwriting activities (Dr. Farrow emphatic). Send drafts for her revision. (email reply, 2026-04-15)
- [ ] **7. Draft 3+ language construction sample lesson plans via ChatGPT** — Currently only 2 examples vs. 5 used for handwriting. Quality will suffer without more. Dr. Farrow approved AI drafting; she'll revise. (email reply, 2026-04-15)

**Multi-grade rollout (K prototype proves viability first):**

- [ ] **8. Extend LC standards file to PreK + 1st grade** — K complete. PreK needs curation from `48-60_Indicators.pdf` (GELDS CLL domain — language-construction-relevant indicators only). 1st grade from `Standards Language Arts_Grade 1.pdf` (expected domains: `1.L.GC`, `1.L.V`, `1.P.AC` — mirror K's narrow filter). Pick up in a fresh chat when 1st/PreK prototype becomes priority. (scope 2026-04-17)

**Async cleanup:**

- [ ] **9. Clarify "FORM J codes" question with Dr. Farrow** — She read "codes in old format" as document formatting and was confused. Re-ask if you meant pedagogical/activity codes; otherwise proceed with old-format sample as-is for AI training. (email reply, 2026-04-15)

**LC generator prompt rules (from Dr. Farrow comments on example lessons, 2025-12-09 / 2026-04-15):**

- [ ] **10. LC param agent intake schema** — Collect: unit focus, vocabulary words, genre (narrative/opinion/informational), sentence structure focus, previously-learned sentence structure, grade, ability level (more support / more challenge / on target). Mirrors handwriting param pattern + adds `previously_learned_structure`. (form-j comment 9 + lesson-plan-k comment 5)
- [ ] **11. Activity naming + FORM K hyperlinks** — Each activity in a generated LC lesson must be hyphenated and linkable to its FORM K description (activity name + suggested level). Same pattern as handwriting activity-framework.md. (form-j comment 81)
- [ ] **12. Generator populates example banks inline** — Activities that reference example sentences/word lists must have real content in a 📝 **Example Bank:** block, not placeholders like "+Additional examples". Appears 3× in Form J — recurring pattern. (form-j comments 89, 149, 225)
- [ ] **13. Always-on Adaptation prompt with vary-by-ability** — Every LC lesson ends with 🔄 **Adaptation:** asking for modifications. Modification types span: activity-level, modeling depth, guided-practice pacing, example intensity. Refer to Science of Learning principles. (form-j comment 292)
- [ ] **14. Strip comments from LC example originals once 10–13 are resolved** — Originals in `language_construction/form-j-example-lesson.md`, `lesson-plan-k-example.md`, and `form-l-modifications.md` still carry Dr. Farrow's comment blockquotes. Once items 10–13 are implemented and validated in the prototype/generator, strip the blockquotes and retire the `prompt-ready/` duplicates. (cleanup, 2026-04-17)
