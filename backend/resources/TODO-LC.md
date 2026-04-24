# Language Construction TODO

<!-- Split from main TODO on 2026-04-19 for focused LC tracking. -->
<!-- Managed by /dev sub-skills. Grouped by phase, checkbox style. -->

> Long-form review notes and cycle walkthroughs live in [`LC-review-tracker.md`](LC-review-tracker.md). This file is for actionable tasks only.

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

## Dr. Farrow LP1 feedback — cycle 4 (2026-04-23)

**Source:** `backend/resources/expert-feedback/dr-farrow-feedback-lc-plants-k-adverbs.md` (19 inline comments on `AI Sample - K Informational - Plants (One-Word Adverbs, More Support).docx`).
**Synthesis:** `LC-review-tracker.md` groups the 19 comments into 15 action items (A.1–E.15) with paragraph citations.
**Primary edit target:** `backend/scripts/prototype_lc_generator.py` — the entire system prompt lives in `SYSTEM_PROMPT_TEMPLATE` (starts ~line 105, rules 1–13 start ~line 146). Rule numbers drift as rules are added — always cite by rule title, not number.
**Rendering decision (2026-04-23):** box Corrective Feedback and Example Bank blocks using markdown blockquote (`> `). Pandoc renders blockquotes as indented Block Text paragraphs in docx — visually distinct without a custom reference docx. Reversible if Dr. Farrow wants stronger separation later.
**Verification pattern per lane:** regenerate the LP 1 input (`info_adverb_support` entry in `INPUTS`) with `prototype_lc_generator.py`, diff new output against the annotated feedback file, confirm each targeted comment is moot.
**Not done tonight:** execution of items 15–29. Session scope tonight was scoping + documentation only; execution happens in a fresh chat once the task list is reviewed.

### Lane 1 — Prompt rule tightening (unblocked, small edits)

- [ ] **15. Cap Guided Practice at exactly 1 activity** — Current Rule 2 says "Each subsection may use 1–2 activities." Split: Review & Connect / Model / Application = 1–2 activities; **Guided Practice = exactly 1**. Rationale: GP is scaffolded practice with teacher taking load away — two activities overloads working memory (current LP 1 has Sentence Hunt + Build-A-Sentence + Partner Talk in one GP, which Dr. Farrow flagged as not GP at all). (tracker A.2, comment para 104)
- [ ] **16. Example Bank placement rule** — Add rule: every 📝 **Example Bank:** block appears *immediately after* the activity script it supports, not floating between activities. Current Rule 2 / component-markers doesn't specify placement. (tracker A.3, comment para 60)
- [ ] **17. Spotlight Sentence same-verb-type constraint** — Add rule: when priming kids on a verb type (action vs. be-verb), all Spotlight Sentence examples must use the same verb type — do NOT mix. Broke priming in current LP 1 ("The sprout is small" inserted into action-verb Spotlight set). (tracker A.5, comment para 53)
- [ ] **18. Wrap-Up comparison target = adjectives (for adverb lessons)** — Current Wrap-Up asks "how are adverbs different from be-verbs?" — should be "from adjectives." Add conditional rule on target-structure → comparison-target mapping. Couples with item 23 (non-example contrast rule) — both use the same target-→-contrast mapping. (tracker A.6, comment para 167)
- [ ] **19. Teacher questions must anchor to the verb** — Add rule: when asking kids "is [word] how/when/where?", reframe as "is [word] showing us HOW it [verb]ed, WHERE it [verb]ed, or WHEN it [verb]ed?" — anchor every answer to the action, not to the word in isolation. Reduces cognitive load. (tracker A.7, comment paras 172 ×2)
- [ ] **20. Objectives: include an "expand sentences using [target structure]" objective** — Augment the Section B guidance line in the prompt (currently just `- **B. Objectives** — Listed in order of difficulty to scaffold mastery.` around line 126 in `SYSTEM_PROMPT_TEMPLATE`'s "Output Structure — MANDATORY" block) to require an expansion-type objective naming the target structure explicitly (e.g., "expand sentences using one-word adverbs"). (tracker E.15, comment para 13)
- [ ] **21. Corrective feedback examples must be natural K errors** — Augment Rule 8: corrective-feedback example errors must reflect real K-child errors (be-verb substitution, adverb-phrase substitution), NOT un-grammatical stubs like "The bloom pink" (no English-speaking K child says this). For the adverb-phrase case specifically, teacher script should affirm ("you just did something really difficult we'll talk about later"), not correct as wrong. (tracker C.12, comment paras 132, 153)
- [ ] **22. Act-It-Out-Quick positioning rule** — Add to Rule 2 (or as a new subsection-ordering rule): when Act-It-Out-Quick is used in Review & Connect, it goes at the *top* (alongside vocab review) OR at the *end* (as a connector). Do NOT insert it between Spotlight Sentence and the D.1 Example Bank. Current LP 1 broke this: Act-It-Out-Quick landed between Spotlight and the Example Bank, which confused Dr. Farrow reading the flow. Couples with item 16 (Example Bank placement) — both are D.1 subsection-ordering rules; can land in the same prompt edit. (tracker A.4, comment para 60)

### Lane 2 — Prompt rule additions (unblocked, needs design)

- [ ] **23. Right-level non-example contrast rule** — Highest-impact regression in LP 1. Prescribed approach (picked 2026-04-23 after audit): add a **table in the prompt** mapping target structure → non-example contrast structure. Proposed K-row contents: adverb → adjective; be-verb → action verb; adjective → action verb; prepositional phrase → single-word adjective. Dr. Farrow's logic: be-verb adverbs in K are often phrases, which introduces cognitive load before kids can distinguish adjectives from adverbs. Generalizes to "every target needs an explicit right-level contrast — don't leave selection to the model." A table is extensible to non-K grades later (PreK / 1st) without rewriting the rule. (tracker A.1, comment paras 84, 91, 167)
- [ ] **24. New component marker `📘 Teacher Note`** — Add to component-markers block in the prompt: `📘 **Teacher Note:** — meta-instructions for the teacher (e.g., "Worked example 1. Listen: ..."), NOT what the teacher says aloud to children.` Distinguishes teacher scaffolding cues from 🗣️ **Teacher:** (child-facing dialogue). **Rendering (criterion):** follow Lane 3 precedent (items 25 + 26 use blockquote for block-level scaffolding markers). Since Teacher Note is inline (one line before a scripted block), not block-level, use inline italics instead: `📘 **Teacher Note:** *[italic meta-instruction]*`. Italic satisfies Dr. Farrow's "different color or bracket" request and pandoc renders it natively in docx without a custom reference template. (tracker B.8, comment paras 74, 84)

### Lane 3 — Markdown rendering convention (unblocked, blockquote)

- [ ] **25. Box Corrective Feedback blocks with blockquote** — Update Rule 8's format spec from:
    ```
    Corrective Feedback: Some children may use an action verb...
    🗣️ **Teacher:** "Remember, a be-verb tells us..."
    ```
    to:
    ```
    > ⚠️ **Corrective Feedback:** Some children may use an action verb...
    >
    > 🗣️ **Teacher:** "Remember, a be-verb tells us..."
    ```
    Both lines inside the blockquote so the whole feedback unit renders as one indented Block Text paragraph in docx. Add `⚠️` prefix so it's scannable in markdown too. (tracker D.13, comment paras 97, 101)
- [ ] **26. Box Example Banks with blockquote** — Update component-markers block + any rule that emits Example Bank. Current format:
    ```
    📝 **Example Bank:** - The seed sprouts today. - The sprout grows slowly.
    ```
    New format:
    ```
    > 📝 **Example Bank:**
    > - The seed sprouts today.
    > - The sprout grows slowly.
    ```
    Bullets inside the blockquote — renders as an indented bulleted list in docx. (tracker D.14, comment para 101)

### Lane 4 — BLOCKED on Form K coordination

These require new activity definitions in Form K. Dr. Farrow is modifying `FORM K_ Scaffolded Activities for Vocabulary & Sentence Structure .docx` in Dropbox (last touched 2026-04-23 14:35) as she reviews LP 2 + LP 3. Per `LC-review-tracker.md` line 62, re-ingesting Form K is on HOLD until all three LP reviews land — editing activity rules now = double work.

**Unblock condition (all three):** (a) Dr. Farrow completes LP 2 + LP 3 review, (b) her Form K docx revision is final, (c) `/dev docs` pipeline re-ingests the updated Form K into `backend/prompt/reference_materials/language_construction/form-k-scaffolded-activities.md`.

- [ ] **27. BLOCKED — Build-A-Sentence worksheet structure** — Add to Form K's middle-level Guided Practice entry: subject picture, space for action verb, space for adverb; each row prompts the adverb question ("how?", "when?", "where?"); encourage invented spelling ("listen to the sounds of sprout, write the sounds you hear"). Currently Form K's Build-A-Sentence definition is: *"Children are guided to create their own sentence by imitating a model (e.g., The whale is a ___)."* — too loose for K-level scaffolding. (tracker C.9, comment paras 114, 135)
- [ ] **28. BLOCKED — Sentence Hunt replaces Same-or-Different in Guided Practice** — Update Form K: promote Sentence Hunt from low-level to the canonical Guided Practice activity for one-word-adverb lessons; contrast sentence must be one-word-adjective. Deprecate / remove Same-or-Different for adverb lessons since Dr. Farrow says it doesn't match GP's "teacher takes away load" intent. (tracker C.10, comment para 91)
- [ ] **29. BLOCKED — Picture Sentence replaces Stretchy Sentence in Application** — Add new Form K entry (Picture Sentence) for Application activities: flow = draw → orally rehearse → write with invented spelling → circle the adverb; teacher walks child through picture → sentence → label noun/verb → pick adverb → write; struggling kids get told *what* to draw. Dr. Farrow's comment #14 includes 8 candidate plant-adverb sentences to seed the Example Bank (lift verbatim). (tracker C.11, comment para 141 ×2)

### Lane 5 — Open design question

- [ ] **30. Confirm Rule 10 standards priority order with Dr. Farrow** — Rule 10 prioritizes GC → V → AC, but the human reference (`lesson-plan-k-example.md`) puts AC first. Ask in next email (same email as item 31's regen ship): which ordering is canonical? **Record answer in both places:** (a) if flipped, update Rule 10 text in `prototype_lc_generator.py`; (b) strike the cross-section TODO under `LC-review-tracker.md` § "Section A — Standards" → "TODOs surfaced" once resolved. Either keep Rule 10 as-is (reference is a one-off) or flip to match reference. (tracker section A cross-section TODO)

### After execution (ship what's fixed)

- [ ] **31. Regenerate all three K LP inputs and re-ship** — After Lane 1 + Lane 2 + Lane 3 (items 15–26) land, run `prototype_lc_generator.py` loop over all three `INPUTS` entries. Push new `.md` + `.docx` outputs to Dropbox folder `AI Generated Lesson Samples/`. Email Dr. Farrow that LP 1 is freshly regenerated with her 19 fixes applied — this round she only needs to review LP 2 + LP 3 (both still on the original generation), and can treat regenerated LP 1 as a validation pass confirming the prompt now produces what she asked for.
