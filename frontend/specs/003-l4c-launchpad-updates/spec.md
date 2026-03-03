# Spec 003: L4C LaunchPad Rename, Sequenced Segmentation Videos & Science of Learning Page

## Overview

Three updates requested by Dr. Farrow ahead of Wednesday teacher demo:

1. **Rename** "AI Teaching Assistant" → "L4C LaunchPad" throughout the UI
2. **Add videos** for Sequenced Segmentation (already uploaded to S3)
3. **New page** — "The Science of Learning: Sequencing a Lesson" explaining the pedagogical logic behind lesson structure

**Source:** Dr. Farrow email (2026-03-02) + Google Doc content

## Implementation Notes

- **No code templates in this spec.** The implementer should read live files via MCP tools (Read, Glob, Grep) before making changes. This avoids stale code snippets.
- **Use Context7 MCP** to pull latest docs for React, Vitest, React Testing Library, Tailwind CSS, and Framer Motion when writing new components or tests. Resolve library IDs first, then query for relevant patterns.
- **Follow existing patterns.** Match the code style, component structure, and Tailwind classes already used in files like `BestPractices.jsx`, `HandwritingSpelling.jsx`, and `videoData.test.js`.

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Rename — Navigation menu label | ✅ Done | `Navigation.jsx` |
| Rename — Nav "Open workspace" button | ✅ Done | `Navigation.jsx` — both desktop + mobile |
| Rename — Nav "View workspace" link | ✅ Done | `Navigation.jsx` — account dropdown |
| Rename — Chatbot greeting message | ✅ Done | `Chatbot.jsx` — both instances |
| Rename — Chatbot header label | ✅ Done | `Chatbot.jsx` |
| Rename — Chatbot2 header label | ✅ Done | `Chatbot2.jsx` |
| Rename — ChatBubble bot name | ✅ Done | `ChatBubble.jsx` |
| Rename — AITeachingAssistant page component | ✅ Kept as-is | No user-visible text; filename + route preserved |
| Rename — Route path | ✅ Kept as-is | `/ai-teaching-assistant` preserved for bookmarks |
| Rename — AboutSection reference | ✅ Done | `AboutSection.jsx` |
| Rename — Tests | ✅ Done | `Chatbot.test.jsx` |
| Videos — Update Sequenced Segmentation in videoData.js | ✅ Done | Removed `noVideoYet`, added 2 S3 URLs |
| New page — Science of Learning | ✅ Done | `ScienceOfLearning.jsx` created |
| New page — Navigation link | ✅ Done | Added between Best Practices and L4C LaunchPad |
| Tests — Update Chatbot.test.jsx | ✅ Done | Updated 3 assertions |
| Tests — Update videoData.test.js | ✅ Done | Asserts 2 videos with valid S3 URLs |
| Tests — New page rendering | ✅ Done | 5 tests in `ScienceOfLearning.test.jsx` |

## Implementation Files

| File | Purpose |
|------|---------|
| `frontend/src/components/Navigation.jsx` | Nav label, buttons, links |
| `frontend/src/components/Chatbot.jsx` | Legacy chatbot greeting + header |
| `frontend/src/components/Chatbot2.jsx` | Lesson generator header |
| `frontend/src/components/ChatBubble.jsx` | Bot name in chat bubbles |
| `frontend/src/components/AboutSection.jsx` | "Lesson Builder" reference |
| `frontend/src/pages/AITeachingAssistant.jsx` | Page wrapper (rename component) |
| `frontend/src/AppRoutes.jsx` | Route path + import |
| `frontend/src/data/videoData.js` | Sequenced Segmentation video URLs |
| `frontend/src/pages/ScienceOfLearning.jsx` | **NEW** — Science of Learning page |
| `frontend/src/test/Chatbot.test.jsx` | Update test assertions |
| `frontend/src/test/ScienceOfLearning.test.jsx` | **NEW** — Science of Learning rendering tests |
| `frontend/src/test/videoData.test.js` | Update Sequenced Segmentation assertion |

---

## Change 1: Rename "AI Teaching Assistant" → "L4C LaunchPad"

Replace every UI-visible occurrence of "AI Teaching Assistant" with "L4C LaunchPad". Also update the "Open workspace" / "View workspace" button text to "Open L4C LaunchPad" / "L4C LaunchPad".

### Files and locations

| File | Location | Old text | New text |
|------|----------|----------|----------|
| `Navigation.jsx` | line 63 — nav item label | "AI Teaching Assistant" | "L4C LaunchPad" |
| `Navigation.jsx` | line 197 — desktop CTA button | "Open workspace" | "Open L4C LaunchPad" |
| `Navigation.jsx` | line 242 — account dropdown link | "View workspace" | "L4C LaunchPad" |
| `Navigation.jsx` | line 370 — mobile CTA button | "Open workspace" | "Open L4C LaunchPad" |
| `Chatbot.jsx` | lines 14, 405 — greeting | "I'm your AI Teaching Assistant" | "I'm the L4C LaunchPad" |
| `Chatbot.jsx` | line 432 — header | "AI Teaching Assistant" | "L4C LaunchPad" |
| `Chatbot2.jsx` | line 855 — header | "AI Teaching Assistant" | "L4C LaunchPad" |
| `ChatBubble.jsx` | line 111 — bot name | "AI Teaching Assistant" | "L4C LaunchPad" |
| `AboutSection.jsx` | line 84 — product name | "L4C's Advanced Lesson Builder" | "The L4C LaunchPad" |
| `Chatbot.test.jsx` | lines 23, 66, 71 — assertions | "AI Teaching Assistant" | "L4C LaunchPad" |

**Note:** `AITeachingAssistant.jsx` has no user-visible text to change (it only renders `<Chatbot2 />`). Keep the component name, filename, and route path (`/ai-teaching-assistant`) as-is to avoid breaking bookmarks.

---

## Change 2: Add Sequenced Segmentation Videos

Two videos have been uploaded to S3:
- `s3://l4c-videos/videos/Sequenced Segmentation.mp4`
- `s3://l4c-videos/videos/Sequenced Segmentation 2.mp4`

### videoData.js — Update Sequenced Segmentation entry (lines 35-40)

- Remove `noVideoYet: true`
- Add 2 videos to the `videos` array using `encodeVideoUrl()`:
  - `Sequenced Segmentation.mp4` — label: "Demonstration 1"
  - `Sequenced Segmentation 2.mp4` — label: "Demonstration 2"
- Follow the same object structure as other practices with videos (e.g., `hold-pencil-correctly`)

---

## Change 3: New Page — "The Science of Learning: Sequencing a Lesson"

### 3a. New file: `frontend/src/pages/ScienceOfLearning.jsx`

Create a new page component with two sections:

**Section 1: "How Learning Sticks"**

Content:

> Learning means developing the ability to retrieve information from long-term memory. So how does information get stored in long-term memory in the first place?
>
> Information is stored when students actively think about it and work with it in their working memory. Repeatedly retrieving previously learned information and using it in different ways — such as comparing, contrasting, connecting, and synthesizing — helps strengthen and solidify that learning over time.
>
> However, teachers must consider potential barriers to this process. Students have a limited amount of space in their working memory. The younger the child, the more limited that space tends to be. Very young children can typically hold only 2–3 pieces of information in mind at once, and there is individual variability, meaning some children can manage more information while others can manage less.
>
> When students are given too much new information or too many steps at once — especially if the material is unfamiliar or not yet mastered — they may experience cognitive overload. Cognitive overload occurs when the amount of information exceeds a student's working memory capacity, leading to confusion, frustration, and interruptions in learning.

**Subheading: "What Does This Mean for Instruction?"**

> To support learning and manage cognitive load, teachers should:

Numbered list:
1. Begin with review. Start lessons with brief, routine retrieval practice that builds fluency and gradually increases in complexity over time.
2. Introduce new learning in small steps. Avoid overwhelming students with too much new information at once.
3. Sequence instruction intentionally. Plan activities that prepare students for the lesson goal and build toward it step by step.
4. Model explicitly. Clearly demonstrate new skills or processes, think aloud, and guide students through each step with feedback.
5. Provide structured practice. Offer ample guided practice before expecting independent work.
6. Support application and transfer. Give students opportunities to apply new learning in meaningful contexts with continued support.
7. Keep students actively engaged. Incorporate frequent opportunities to respond so students remain attentive and cognitively involved.

**Section 2: "L4C LaunchPad"**

> The L4C LaunchPad helps you quickly create lessons using the L4C approach and what we know about how children learn best.
>
> Every lesson includes five simple parts:

**1. Review & Connect**
> Start with a short review of important prior learning.
> This helps children:
> - Remember what they already know
> - Connect past learning to today's lesson
> - Feel prepared for new content

**2. Model, Explain, Engage**
> This is the teaching part of the lesson.
>
> You:
> - Clearly explain the new concept or skill
> - Model your thinking out loud
> - Give clear definitions
> - Share examples and non-examples
>
> Students:
> - Actively respond
> - Practice thinking about the new idea
> - Stay engaged through multiple opportunities to participate

**3. Guided Practice**
> Now students practice — with your support.
>
> You:
> - Break the skill into small, manageable steps
> - Guide students through each step
> - Provide immediate feedback
> - Correct misunderstandings right away
>
> The goal is to build accuracy and confidence.

**4. Application**
> Students apply the new skill in a slightly different or more challenging situation.
>
> You continue to:
> - Provide support
> - Ask guiding questions
> - Help students transfer their learning

**5. Wrap-Up**
> End the lesson by:
> - Reviewing what students learned
> - Reinforcing the key idea
> - Celebrating their effort and progress
>
> This helps strengthen learning and builds confidence.

### Design notes

- Follow the same layout pattern as existing content pages (e.g., `BestPractices.jsx`)
- Use the existing Tailwind utility classes and design system (gradient headers, rounded cards, etc.)
- Page title: "The Science of Learning: Sequencing a Lesson"
- Each of the 5 lesson parts should be visually distinct (numbered cards or accordions)
- Use icons from lucide-react where appropriate (Brain, BookOpen, Target, etc.)

### 3b. AppRoutes.jsx — Add route

- Import the new `ScienceOfLearning` page component
- Add a route at path `science-of-learning` — no authentication required (educational content, like Best Practices)

### 3c. Navigation.jsx — Add nav item

- Add "Science of Learning" to the `navItems` array, between "Best Practices Modeled" and "L4C LaunchPad"
- href: `/science-of-learning`
- No dropdown — simple link like "Homepage"

---

## Tests

### Updated Tests

**`Chatbot.test.jsx`** — Update 3 assertions from "AI Teaching Assistant" → "L4C LaunchPad"

**`videoData.test.js`** — Update the Sequenced Segmentation test (lines 36-40):
- Current test asserts `noVideoYet: true` and empty videos
- New test should assert: `noVideoYet` is undefined, 2 videos present, both have valid S3 URLs

### New Tests

**`frontend/src/test/ScienceOfLearning.test.jsx`** — Basic rendering tests:

| Test | What it verifies |
|------|-----------------|
| Page title renders | "The Science of Learning: Sequencing a Lesson" appears |
| "How Learning Sticks" section renders | Section heading is present |
| All 5 lesson parts render | "Review & Connect", "Model, Explain, Engage", "Guided Practice", "Application", "Wrap-Up" are all present |
| "L4C LaunchPad" section renders | Section heading mentions "L4C LaunchPad" |
| Instructional strategies list renders | All 7 items present (Begin with review, Introduce new learning, etc.) |

### Running Tests

```bash
# All frontend tests
cd frontend && npm test

# Just the spec 003 affected tests
cd frontend && npx vitest run src/test/Chatbot.test.jsx src/test/ScienceOfLearning.test.jsx src/test/videoData.test.js
```

---

## Summary of All Changes

| # | Change | Action | File(s) |
|---|--------|--------|---------|
| 1a | Nav menu label | RENAME → "L4C LaunchPad" | Navigation.jsx |
| 1b | Nav CTA buttons | RENAME → "Open L4C LaunchPad" | Navigation.jsx |
| 1c | Chatbot greeting | RENAME → "L4C LaunchPad" | Chatbot.jsx |
| 1d | Chatbot header | RENAME → "L4C LaunchPad" | Chatbot.jsx |
| 1e | Chatbot2 header | RENAME → "L4C LaunchPad" | Chatbot2.jsx |
| 1f | ChatBubble bot name | RENAME → "L4C LaunchPad" | ChatBubble.jsx |
| 1g | About section reference | RENAME → "The L4C LaunchPad" | AboutSection.jsx |
| 1h | Tests | UPDATE assertions | Chatbot.test.jsx |
| 2b | Tests | UPDATE Sequenced Segmentation assertion | videoData.test.js |
| 2 | Sequenced Segmentation | ADD 2 video URLs, remove noVideoYet | videoData.js |
| 3a | Science of Learning page | CREATE new page component | ScienceOfLearning.jsx |
| 3b | Route | ADD `/science-of-learning` | AppRoutes.jsx |
| 3c | Navigation | ADD "Science of Learning" nav item | Navigation.jsx |
| 3d | Tests | ADD rendering tests | ScienceOfLearning.test.jsx |

---

## Verification

### Automated Tests
```bash
cd frontend && npx vitest run src/test/Chatbot.test.jsx src/test/ScienceOfLearning.test.jsx src/test/videoData.test.js
```

### Manual Test
```bash
docker compose down && docker compose up -d --build
docker compose exec backend python scripts/init_db.py
open http://localhost:3000
```

### Expected Output

**Navigation:**
- [ ] Menu shows: Homepage | Best Practices Modeled | Science of Learning | L4C LaunchPad
- [ ] "L4C LaunchPad" links to `/ai-teaching-assistant`
- [ ] "Science of Learning" links to `/science-of-learning`
- [ ] Authenticated user sees "Open L4C LaunchPad" button (not "Open workspace")
- [ ] Account dropdown shows "L4C LaunchPad" link (not "View workspace")
- [ ] Mobile menu shows same labels

**Chatbot / L4C LaunchPad (`/ai-teaching-assistant`):**
- [ ] Header says "L4C LaunchPad" (not "AI Teaching Assistant")
- [ ] Greeting says "I'm the L4C LaunchPad" (not "AI Teaching Assistant")
- [ ] Bot name in chat bubbles says "L4C LaunchPad"

**Sequenced Segmentation (`/handwriting-spelling/sequenced-segmentation`):**
- [ ] Video player loads (not "coming soon")
- [ ] Two videos available: "Demonstration 1" and "Demonstration 2"
- [ ] Both videos play from S3

**Science of Learning (`/science-of-learning`):**
- [ ] Page loads with title "The Science of Learning: Sequencing a Lesson"
- [ ] "How Learning Sticks" section with cognitive load content
- [ ] 7 instructional strategies listed
- [ ] "L4C LaunchPad" section with 5 lesson parts
- [ ] Each lesson part has title, description, and bullet points
- [ ] Page accessible without login

**No regressions:**
- [ ] All existing video pages still work
- [ ] About section updated text renders correctly
- [ ] Login/signup flow unchanged
- [ ] No console errors

---

## Spec Revisions

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-03-02 | Initial draft — all 3 changes from Dr. Farrow email |
| 1.0 | 2026-03-02 | Implemented — all 3 changes complete, 38/38 tests passing |
