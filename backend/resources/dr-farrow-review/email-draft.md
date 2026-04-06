# Email Draft — Dr. Farrow Lesson Plan Review

**Subject:** Updated AI Lesson Plans Ready for Review (April 2026)

---

Dr. Farrow,

Apologies for the delay — this update took longer than expected to get right. I've uploaded 5 updated lesson plans to our shared Dropbox folder for your review. Each file includes the teacher's input (questions and answers) at the top, followed by the generated lesson plan with images.

**Dropbox folder:** [AI Lesson Review - April 2026](https://www.dropbox.com/scl/fo/u7dqleh0dfrdawfhirhls/ADOAh-4-H6hAQTfIsecQHmQ?rlkey=7w96ta39u2mv02lqs10ibmt5q&st=u5fkirhr&dl=0)

**Files:**
1. `prek_letter_z_onlevel_mid.docx` — PreK, letter Z, on-level
2. `k_letter_b_onlevel_mid.docx` — Kindergarten, letter B, on-level
3. `k_letter_b_struggling_mid.docx` — Kindergarten, letter B, struggling
4. `k_letter_b_onlevel_scaffolded.docx` — Kindergarten, letter B, on-level (scaffolded)
5. `first_letter_i_onlevel_mid.docx` — 1st Grade, letter I, on-level

Please add your comments directly in the Word documents. I'll pull them once you're done.

---

## What Changed Since Last Time

**New: Activity Planner pipeline** — The AI now has a two-stage process. First, an Activity Planner selects activities and makes all pedagogical decisions (scaffolding level, guided practice techniques, spelling patterns, etc.). Then the generator executes that plan. This means the generator no longer guesses — it follows a structured plan.

**Key improvements:**
- **1st grade lessons now teach CVCe (magic-e) patterns** — Previously, 1st grade vowel lessons produced basic intro lessons instead of the CVC vs CVCe contrast patterns appropriate for that level. The planner now identifies the correct spelling pattern (e.g., CVCe for 1st + vowel + on-level) and the generator produces contrast word pairs (pip/pipe, kit/kite).
- **Guided Practice now has 3 sub-activities** — The planner specifies an ordered list of techniques (e.g., cover-and-try, say-and-write, write-and-sound), matching expert lesson density.
- **New intake questions** — The AI now asks teachers about previously learned sounds and skill focus before generating. This ensures word choices only use sounds the students actually know.
- **Reduced token cost** — The generator prompt now only loads the activity descriptions it actually needs (dispatcher pattern) instead of the entire activity framework. This trims the system prompt significantly, bringing generation cost down to ~$0.18 per lesson.
- **Upgraded to GPT-5.4 model family** — All nodes upgraded from GPT-4o/5.1 to GPT-5.4 for improved instruction quality.

---

## Generation Cost

Each lesson takes about 40,000 tokens and costs ~$0.18 to generate (GPT-5.4):

| Lesson | Tokens | Cost |
|--------|--------|------|
| PreK, letter Z | 43,777 | $0.19 |
| K, letter B, on-level | 39,683 | $0.18 |
| K, letter B, struggling | 40,168 | $0.19 |
| K, letter B, scaffolded | 37,903 | $0.17 |
| 1st, letter I | 39,455 | $0.17 |
| **Average** | **40,197** | **$0.18** |

---

## Expert Examples — Please Update

The AI now asks two new questions that weren't part of the original examples:
- **"What sounds/letters have the students already learned?"**
- **"What skill would you like to focus on?"** (isolating sounds, blending, letter formation, or spelling)

I've copied the existing expert examples into a subfolder. Could you update them to include answers to these new questions? This will help us keep the AI's output aligned with your expectations.

**Subfolder:** `Expert Examples (Please Update)` (inside the same Dropbox folder)

**Files to update:**
1. `FORM C_ Example Handwriting & Spelling Lesson for Output .docx`
2. `Further example lesson plans Transcription.docx`
3. `First grade scripted lesson .docx`

For each example, just add what sounds/letters would have been previously taught and what skill the lesson focuses on — same format as the Q&A table at the top of the new lesson plans.

---

Looking forward to your feedback!

Naimul
