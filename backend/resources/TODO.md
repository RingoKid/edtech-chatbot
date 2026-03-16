# Project TODO

<!-- Managed by /dev sub-skills. Grouped by source, checkbox style. -->

## Reference Material Updates (Dr. Farrow, 2026-03-16)

- [ ] **Update Form D** — Dropbox version has major changes: 13 activities removed, 10 added, 4 renamed, most grade/level annotations removed. Cannot just swap the file — generator prompt rules (lines 74-80 in handwriting_generator.py) reference level tags that no longer exist. Needs coordinated update with prompt rules.
- [ ] **Add Activity Framework** — New file from Dr. Farrow. 193 paragraphs of cognitive rationale for when/why each activity is appropriate. Not in codebase yet. Dropbox: `Activity Framework Transcription.docx`. Converted markdown at `/tmp/activity-framework.md`.
- [ ] **Add First Grade Scripted Lesson** — Dr. Farrow's hand-written reference lesson (3 comments, Feb 21). Not in codebase. Dropbox: `First grade scripted lesson .docx`. Converted markdown at `/tmp/first-grade-scripted-lesson.md`.

## Generator Prompt Changes (Dr. Farrow feedback, 2026-03-09)

- [ ] **AI does not prompt for previously learned skills** — "kinda screwed up the activity selection" (kindergarten test plan comment #1, email #2)
- [ ] **Review section incorrect** — Generator confuses what Review is. Review = going through previously learned letter-sounds with a focus on sounds. Generator was introducing the new letter in Review instead. (comments #3, #4)
- [ ] **Activity name confusion** — Generator labels activities with wrong names (e.g., says "Sound Spark" but describes "Sound Echo", says "Sound Hunt" but it's actually a different activity). (comments #5, #6)
- [ ] **Form B explanations not verbatim** — Generator writes "(Use the exact Form B explanation for Section X here)" placeholder instead of the actual text. (comments #2, #8, #14, #18)
- [ ] **Lowercase only by default for K** — "should just focus on lowercase unless teacher specifies they want uppercase as well" (comment #10)
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

## Eval Maintenance

- [ ] **Regenerate fixtures after Form D + prompt changes** — Current fixtures will be stale once generator behavior changes
- [ ] **Update activity_naming rubric** — Activity names changed (renames, removals, additions in Form D)
- [ ] **1st grade marker formatting** — 53-62% structure score, uses `[Explanation:]` instead of emoji markers
- [ ] **Add eval for previously-learned-skills prompting** — New behavior, needs validation

## Existing TODO (from memory)

- [ ] **Add skill focus intake question** — Dr. Farrow approved. Options: isolating sounds, blending, letter formation, spelling. Not yet implemented.
