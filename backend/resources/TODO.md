# Project TODO

<!-- Managed by /dev sub-skills. Grouped by source, checkbox style. -->

## Async/Performance Fixes (audit, 2026-03-17)

- [x] **Sync DynamoDB calls block event loop** — `chat_history_service.py`, `auth_service.py`, `feedback_service.py` all declare `async def` but call blocking boto3 methods (`table.put_item`, `table.query`, etc.). Every DB call serializes the event loop — 2 concurrent users block each other. Fix: wrap in `asyncio.to_thread()` or switch to `aioboto3`.
- [x] **Graph nodes use sync `.invoke()` in async context** — `graph.py` nodes (`routing_agent_node`, `param_agent_node`, `handwriting_generator_node`, `feedback_collector_node`) call `agent.invoke()` synchronously. The outer `handle_message()` uses `await graph.ainvoke()` but each node blocks the loop during LLM calls. Fix: switch to `await agent.ainvoke()` and make nodes async.
- [x] **Fire-and-forget image generation task** — `image_director.py:99-101` creates background task with `asyncio.create_task()` but never awaits or handles errors. Graph returns before images exist; failures are silent. Fix: await the task or add error handling + logging.
- [x] **Module-level blocking DynamoDB import** — `database.py:38-41` calls `get_dynamodb_resource()` and `dynamodb.Table()` at import time. If DynamoDB is slow/unavailable, entire app hangs on startup. Fix: lazy-load on first request.
- [x] **Graph lazy-init race condition** — `chat_service.py:33-40` `_get_graph()` checks `if self._graph is None` without a lock. Concurrent requests can call `create_graph()` multiple times. Fix: use `asyncio.Lock`.
- [x] **Mixed sync/async graph node signatures** — `graph.py` has some nodes sync, some async (`image_director_node`, `image_assembly_node`). LangGraph handles this but it's inconsistent and error-prone. Fix: make all nodes async.
- [x] **Deprecated `asyncio.get_event_loop()`** — `image_service.py:204` uses deprecated pattern. Fix: use `asyncio.get_running_loop()`.
- [x] **No app lifecycle handlers** — `main.py` has no startup/shutdown hooks. Langfuse client never flushed, DynamoDB connections never closed, background tasks not cancelled on shutdown. Fix: add FastAPI lifespan context manager.
- [x] **Blocking password hashing in async routes** — `auth.py` calls bcrypt `get_password_hash()` / `verify_password()` synchronously in async route handlers. CPU-bound, blocks event loop under load. Fix: wrap in `asyncio.to_thread()`.

## Reference Material Updates (Dr. Farrow, 2026-03-16)

- [x] **Update Form D** — Replaced by activity-framework.md + activity-index.yaml in spec 023. Form D still on disk for reference but no longer loaded by generator or evals.
- [x] **Add Activity Framework** — Added as `activity-framework.md` with slug headings for regex extraction. Used by planner and generator via dispatcher pattern. (commits `284302f`, `bc3406e`)
- [ ] **Add First Grade Scripted Lesson** — Dr. Farrow's hand-written reference lesson (3 comments, Feb 21). Not in codebase. Dropbox: `First grade scripted lesson .docx`. Converted markdown at `/tmp/first-grade-scripted-lesson.md`.

## Generator Prompt Changes (Dr. Farrow feedback, 2026-03-09)

- [x] **AI does not prompt for previously learned skills** — Fixed in spec 023. Added `previously_learned` intake question + Rule 12 constrains word choices to taught sounds only.
- [x] **Activity name confusion** — Fixed by planner pipeline. Activities selected by slug, descriptions extracted by regex, names displayed from framework headings. Activity naming eval now scores 100%.
- [ ] **Review section incorrect** — Generator confuses what Review is. Review = going through previously learned letter-sounds with a focus on sounds. Generator was introducing the new letter in Review instead. (comments #3, #4)
- [ ] **Form B explanations not verbatim** — Generator writes "(Use the exact Form B explanation for Section X here)" placeholder instead of the actual text. (comments #2, #8, #14, #18)
- [x] **Lowercase only by default for K** — Resolved: letter case determined by teacher input (lowercase `b` → lowercase lesson, uppercase `B` → uppercase). Removed `.upper()` calls in generator. (spec 023 phase 2)
- [ ] **Verbal cues not populated** — Generator writes placeholder instead of actual cues from Form F. "The generator should either use the verbal cue or create its own" (comments #11, #12)
- [ ] **Guided practice sequencing wrong for K** — "by kindergarten they should be able to first trace then try their own on level — if children are struggling learners then air writing is more appropriate to begin" — Magic Finger Write not appropriate for on-level K. (comment #13)
- [ ] **Trace & Say confusion** — "trace and say means kids are actually writing, pencil in hand" — generator showed finger-on-picture instead. (comment #15)
- [ ] **Say sound while writing, not letter name** — "say the sound /b/ while writing the letter — you don't want to overwhelm kids switching between saying letter/sound" (comment #17)
- [ ] **Application section had no priming** — "there was no priming for this — illogical sequence — teacher did not say children were at the point of CVC words" (comment #19)
- [ ] **Need to prompt for previously learned skills** — Required so AI can select logical activity sequences and appropriate word examples. (comments #19, #21)
- [ ] **Teacher giving away answers** — "teacher is already telling them the answer — we want kids to match the sound to the letter" (comment #22)
- [ ] **Word choice issues** — "on is not a good word choice because it doesn't follow regular decoding rules" (rubric comment #3)
- [ ] **Sound/letter comparison inappropriate without prior teaching** — "this would not be appropriate if the teacher did not indicate that this sound was already learned" (comment #9)

## Layout/UX Changes (Dr. Farrow feedback, 2026-03-09)

- [ ] **Corrective feedback should be boxed** — "teachers know it is not part of the lesson but is a way teachers can correct misunderstandings" (rubric comment #1)
- [ ] **Add boxed section for possible words/sounds** — "Teachers like to see that" — after each activity, show all possible words/letter sounds to use. (rubric comment #1)

## Bug Fixes (Dr. Farrow, 2026-03-14)

- [ ] **Old lesson plan conversations not shown in queue** — "my old lesson plans 'conversations' are not being shown in the queue" (email #4, Mar 14)

## Activity Planner (spec 023, 2026-04-03)

- [x] **Fix standards selection pipeline** — Implemented: `extract_standard()`, `validate_plan_standards()`, planner prompt with grade-filtered standards, generator Rule 5 rewritten to use pre-selected standards. All 34 codes validated, fabricated codes eliminated. (commit `ee66f1f`)
- [x] **Update activity_naming eval rubric** — All 5 eval rubrics updated from Form D to activity-framework.md. Eval runner loads `activity-framework.md` instead of `form-d-scaffolded-activities.md`. Activity naming now scores 100%. (commit `3572ca1`)
- [x] **Update eval Pydantic models** — `tests/evals/models.py` field descriptions updated from "Form D" to "activity framework". (commit `98b99d1`)
- [x] **Upgrade models to GPT-5.4 family** — All nodes upgraded: routing/param/planner/feedback → gpt-5.4-mini, generator → gpt-5.4. Model registry updated with pricing. (commits `e32dd48`, `98b99d1`)
- [x] **Regenerate all fixtures** — Stale fixtures removed. 5 expert-mirror fixtures regenerated with directive pipeline (2026-04-06). `k_letter_b_struggling_mid` now works.
- [ ] **Add eval for previously-learned-skills prompting** — New behavior from spec 023, needs validation that generator only uses sounds from `previously_learned` list in example words.

## Generator Quality Issues (expert comparison, 2026-04-06)

Post-directive changes: Structure 100% (all 5 fixtures). Expert comparison scores: PreK/Z 8/10, K/B on-level 7.5/10, K/B struggling 7/10, K/B scaffolded 7.5/10, **1st/I 8/10** (was 4/10). Remaining gaps:

- [x] **1st grade produces intro lesson instead of CVCe** — Fixed by lesson directives (spec 023 phase 2). Planner now outputs `spelling_pattern: CVCe` for 1st + vowel + on-level. Generator contrasts CVC vs CVCe pairs (pip/pipe, kit/kite). Score: 4/10 → 8/10.
- [x] **Guided Practice density** — Fixed by `guided_practice_techniques` directive. Planner specifies ordered technique list (e.g., `[cover_and_try, say_and_write, write_and_sound]`). Generator now produces 3 sub-activities matching expert.
- [ ] **No lesson variant awareness** — Expert "scaffolded" variant uses pre-filled vowels in Application (only write consonants, vowel pre-populated in Elkonin box). Generator has no concept of this — produces standard CVC encoding. May need a `lesson_variant` or `scaffolding_level` parameter.
- [ ] **Word list poverty** — AI uses 3-7 words per lesson; expert uses 11-14. K/B struggling: AI 3 words vs expert 14 minimal pairs. Generator should produce 10+ real words using only `previously_learned` sounds.
- [ ] **Teacher voice too clinical** — AI says "That is correct because..." Expert says "Kiss your brains", "put your listening ears on." Consistent across all grades. Classroom warmth markers missing.
- [ ] **Planner `first_r_advanced` spelling_pattern bug** — Planner returns `CVCe` for 1st + consonant R + advanced. Should be `CVC`/`CCVC`/`CVCC`. Prompt over-applies vowel rule to consonants. (planner directives eval, 3/3 runs failed)

## Param Agent (2026-04-06)

- [ ] **Param agent skips previously_learned and skill_focus** — Agent submits tool call after collecting just grade + letter, skipping optional fields. Root cause: Pydantic schema had `default=[]` and `default="isolating_sounds"`. Defaults removed — agent now must provide all fields. But no multi-turn eval exists to catch this regression.
- [ ] **Update param eval to check all 5 fields** — `params_to_dict()` in `test_param_agent.py` only checks grade/letter/student_level. Must add `previously_learned` and `skill_focus`.
- [ ] **Add multi-turn param eval** — Test that agent asks all questions before submitting. Flow: send grade → assert no submission → send letter → assert no submission → send previously_learned → assert no submission → send skill_focus → assert extraction with all 5 fields. Current eval only tests single-message extraction.
- [ ] **Add "partial info should not submit" test cases** — Cases like "PreK letter m" (has grade + letter but missing previously_learned/skill_focus) should assert `handwriting_params is None` — agent should ask follow-ups, not submit.

## Eval Maintenance

- [ ] **1st grade marker formatting** — 53-62% structure score, uses `[Explanation:]` instead of emoji markers
- [ ] **Update scaffolding eval Pydantic models** — `Activity.difficulty_level` still uses `Literal["low", "middle", "high"]` from old Form D system. Framework uses rank (1-7). Judge maps rank→labels naturally for now but schema should align with rank system eventually.

## DevOps (2026-03-24)

- [ ] **Get OpenAI Admin API key for billing checks** — Need to contact Dr. Farrow. Current `/dev health` only validates the key works; with an Admin key we can check account balance/spend via `/v1/organization/costs`. Add to `/dev health` once obtained.

## Existing TODO (from memory)

- [x] **Add skill focus intake question** — Implemented in spec 023 (activity planner). Added to `HandwritingParams` and param agent.
