# Spec 002: L4C Revision to Pages — Best Practices & Transcription

## Overview

Update the Best Practices overview page and Transcription (Handwriting & Spelling) page to align with the revised L4C content document. Changes include renaming categories, reordering sections, updating descriptions, revising intro copy, and adding a missing practice.

**Source document:** `docs/L4C Revision to Pages.docx`

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| Best Practices — Update page heading | ✅ Done | `BestPractices.jsx` — "Best Practices Modeled" |
| Best Practices — Reverse category order | ✅ Done | `BestPractices.jsx` — Idea Gen → Language Construction → Transcription |
| Best Practices — Update intro copy | ✅ Done | `BestPractices.jsx` — 3 text blocks updated |
| Best Practices — Rename categories | ✅ Done | `BestPractices.jsx` — Titles renamed |
| Navigation — Rename dropdown labels | ✅ Done | `Navigation.jsx` — Labels, order, and hrefs fixed |
| videoData.js — Rename category metadata | ✅ Done | `videoData.js` — categoryInfo titles updated |
| videoData.js — Update Transcription descriptions | ✅ Done | `videoData.js` — All 9 descriptions updated |
| videoData.js — Add "Sequenced Segmentation" | ✅ Done | `videoData.js` — Index 3, noVideoYet: true |
| videoData.js — Update Transcription page intro | ✅ Done | `videoData.js` — Two-element description array |
| HandwritingSpelling.jsx — Handle array description | ✅ Done | `HandwritingSpelling.jsx` — Array.isArray check |
| Unit tests — videoData integrity | ✅ Done | `videoData.test.js` — 11 tests |
| Unit tests — BestPractices rendering | ✅ Done | `BestPractices.test.jsx` — 5 tests |

## Implementation Files

| File | Purpose |
|------|---------|
| `frontend/src/pages/BestPractices.jsx` | Page heading, category order, intro copy, card titles/descriptions |
| `frontend/src/components/Navigation.jsx` | Dropdown menu labels and order |
| `frontend/src/data/videoData.js` | Practice descriptions, category metadata, new practice |
| `frontend/src/pages/HandwritingSpelling.jsx` | Render array-based description as two paragraphs |
| `frontend/src/test/videoData.test.js` | Data integrity tests for videoData.js |
| `frontend/src/test/BestPractices.test.jsx` | Rendering tests for BestPractices page |

---

## Change 1: BestPractices.jsx — Update Page Heading

Change the `<h1>` from **"Research-Backed Practices Modeled"** to **"Best Practices Modeled"** to match the doc's page title.

---

## Change 2: BestPractices.jsx — Reverse Category Order & Rename

The `practicesSections` array currently orders categories as: Handwriting and Spelling → Vocabulary and Syntax → Idea Organization and Generation.

**New order** (left-to-right per the doc):

| Position | New Title | Icon (keep existing) | Route (unchanged) |
|----------|-----------|------|-------|
| 1 | Idea Generation & Organization | Lightbulb | `/idea-generation` |
| 2 | Language Construction | BookOpen | `/vocabulary-syntax` |
| 3 | Transcription | PenTool | `/handwriting-spelling` |

Rename the titles but keep the existing card descriptions and routes unchanged.

---

## Change 3: BestPractices.jsx — Update Intro Copy

Three text blocks need updating:

**Opening paragraph** (currently "Navigate through these three strategies...") → Replace with:
> To compose text children need to generate ideas for a specific purpose (idea generation & organization), translate those ideas into language forms (language construction), and transcribe those ideas into printed text (transcription).

**Research paragraph** — two changes:
- Bold terms become: **idea generation & organization**, **language construction**, **transcription**
- "executive functioning" → "early writing ability"

Full new text:
> Research shows that when teachers embed direct instruction in **idea generation & organization**, **language construction**, and **transcription** within authentic writing tasks, children make faster gains in literacy, language, and early writing ability.

**CTA paragraph** (currently "Click on each component...") → Replace with:
> Find out the early language and literacy skills to target and best practices associated with helping kids learn those skills.

---

## Change 4: Navigation.jsx — Update Dropdown Labels

In the `navItems` array, update the "Best Practices Modeled" dropdown:

| Position | New Label | href |
|----------|-----------|------|
| 1 | Idea Generation & Organization | `/idea-generation` |
| 2 | Language Construction | `/vocabulary-syntax` |
| 3 | Transcription | `/handwriting-spelling` |

**Also fix:** The current Vocabulary and Idea Gen entries use legacy `/videos/` paths that redirect. Use the canonical paths directly.

---

## Change 5: videoData.js — Rename Category Metadata

In the `categoryInfo` object:

- `transcription.title`: "Handwriting & Spelling" → **"Transcription"**
- `language-construction.title`: "Vocabulary & Syntax" → **"Language Construction"**
- `idea-generation`: No changes (doc doesn't cover this page)

**Transcription description** — change from a single string to a **two-element array** with these paragraphs:

> Paragraph 1: "To transcribe language into text, children coordinate phoneme–grapheme correspondences with the motor processes required for handwriting and spelling. Instructional targets include letter knowledge, accurate letter formation, phonemic awareness, sound–letter correspondences, directionality, and print conventions."

> Paragraph 2: "The following practices help teachers optimize instruction to strengthen children's recall and written production of sound–letter correspondences, supporting their ability to write words and sentences with increasing accuracy and fluency."

Routes stay the same (`/handwriting-spelling`, `/vocabulary-syntax`, `/idea-generation`) to avoid breaking bookmarks.

---

## Change 5b: HandwritingSpelling.jsx — Handle Array Description

The Transcription page renders `category.description` as a single `<p>`. Update it to handle both strings and arrays:
- If `description` is an array, render each element as a separate `<p>` tag
- If `description` is a string, render as before (backwards compatibility for other category pages)

---

## Change 6: videoData.js — Update Transcription Practice Descriptions

Update all 9 existing practice descriptions in the `transcriptionVideos` array to match the doc's instructional phrasing:

| Practice | New Description |
|----------|-----------------|
| Hold Pencil Correctly | "Teach the proper way to hold a pencil." |
| Directionality | "Support writing within lines from left to right." |
| Pronounce, Identify, & Isolate Phonemes | "Help children pronounce, identify, and isolate phonemes correctly." |
| Correct Letter Sequence of Strokes | "Teach how to form each letter representing a phoneme step by step, showing the exact order and direction of the strokes." |
| Compare and Contrast Letter Forms | "Talk with children about how letters look—compare their shapes and the strokes used to write them." |
| Retrieve and Connect Phoneme-Grapheme Patterns | "Have children retrieve prior phoneme-grapheme knowledge and connect to new phoneme-grapheme patterns." |
| Apply Phoneme Grapheme Patterns | "Cue children to apply phoneme-grapheme patterns during activities." |
| Corrective Feedback | "Provide corrective and confirmatory feedback explaining what part is incorrect and showing them how to fix it." |
| Encourage Invented Spelling | "Encourage children to use what they've learned about sounds, spelling patterns, and word parts to try spelling new words—even if they're not sure (invented spelling)." |

---

## Change 7: videoData.js — Add "Sequenced Segmentation" Practice

Insert a new practice between "Pronounce, Identify, & Isolate Phonemes" and "Correct Letter Sequence of Strokes" (position 4 in the `transcriptionVideos` array).

- **id:** `sequenced-segmentation`
- **title:** Sequenced Segmentation
- **description:** "Have children pull apart the individual sounds in spoken words in a systematic sequence from easier to more complex forms."
- **noVideoYet:** true
- **videos:** empty array

This follows the same `noVideoYet` pattern as the existing `connecting-words` practice in Language Construction.

---

## Tests

Testing infra: Vitest + React Testing Library + jsdom (already configured in `vitest.config.js`). Run with `npm test` from the `frontend/` directory.

### Test File 1: `frontend/src/test/videoData.test.js` — Data Integrity

Pure JS tests against the exported data arrays. No DOM or React needed.

| Test | What it verifies |
|------|-----------------|
| Transcription practices are in correct order | `transcriptionVideos` IDs appear in this exact order: `hold-pencil-correctly`, `directionality`, `pronounce-identify-isolate-phonemes`, `sequenced-segmentation`, `correct-letter-sequence-strokes`, `compare-contrast-letter-forms`, `retrieve-connect-phoneme-grapheme`, `apply-phoneme-grapheme-patterns`, `corrective-feedback`, `encourage-invented-spelling` |
| Transcription array has 10 practices | 9 original + Sequenced Segmentation |
| Sequenced Segmentation is at index 3 | Inserted between Phonemes and Strokes |
| Sequenced Segmentation has `noVideoYet: true` and empty videos | Matches the `connecting-words` pattern |
| All Transcription descriptions match doc | Exact string match for each of the 10 descriptions against the expected values from the source document |
| `categoryInfo.transcription.title` is "Transcription" | Not "Handwriting & Spelling" |
| `categoryInfo['language-construction'].title` is "Language Construction" | Not "Vocabulary & Syntax" |
| `categoryInfo.transcription.description` is a two-element array | Paragraph structure preserved, not a single string |
| Each paragraph of Transcription description starts with expected text | Paragraph 1 starts with "To transcribe language into text", Paragraph 2 starts with "The following practices" |
| All practices with videos have valid S3 URLs | Every `url` in every video entry starts with `https://l4c-videos.s3.amazonaws.com/videos/` |
| No duplicate practice IDs across all categories | Combine all three arrays, check all `id` fields are unique |

### Test File 2: `frontend/src/test/BestPractices.test.jsx` — Rendering

React Testing Library component tests. Requires `MemoryRouter` wrapper for `<Link>` components.

| Test | What it verifies |
|------|-----------------|
| Page heading renders "Best Practices Modeled" | Find `<h1>` and assert text content |
| Categories render in correct order | Query all category card titles, assert DOM order is: "Idea Generation & Organization", "Language Construction", "Transcription" |
| Intro paragraph mentions composing processes | Assert text contains "idea generation & organization", "language construction", "transcription" |
| Research paragraph says "early writing ability" | Assert text contains "early writing ability", does NOT contain "executive functioning" |
| CTA text matches doc | Assert text contains "Find out the early language and literacy skills" |

### Running Tests

```bash
# All tests
cd frontend && npm test

# Just the spec 002 tests
cd frontend && npx vitest run src/test/videoData.test.js src/test/BestPractices.test.jsx
```

---

## Summary of All Changes

| # | Section | Action | File |
|---|---------|--------|------|
| 1 | Best Practices — page heading | UPDATE to "Best Practices Modeled" | BestPractices.jsx |
| 2 | Best Practices — category order | REVERSE + RENAME titles | BestPractices.jsx |
| 3 | Best Practices — intro copy | UPDATE 3 text blocks | BestPractices.jsx |
| 4 | Navigation — dropdown labels | RENAME + REORDER + fix hrefs | Navigation.jsx |
| 5 | Category metadata | RENAME titles, UPDATE Transcription description to array | videoData.js |
| 5b | Transcription page rendering | HANDLE array description with separate `<p>` tags | HandwritingSpelling.jsx |
| 6 | Transcription practice descriptions | UPDATE all 9 descriptions | videoData.js |
| 7 | Sequenced Segmentation | ADD new practice (no video) | videoData.js |
| 8 | Unit tests — data integrity | ADD 11 tests | videoData.test.js |
| 9 | Unit tests — page rendering | ADD 5 tests | BestPractices.test.jsx |

**Scope note:** The doc only covers the Best Practices overview and Transcription pages. Language Construction and Idea Generation page content are **not** changed by this spec.

---

## Decision: Video URLs (Dropbox vs S3)

The source document contains **Dropbox** video links. The frontend currently serves videos from **AWS S3** (`https://l4c-videos.s3.amazonaws.com/videos/`). These appear to be the same videos hosted in two locations.

**Decision:** Keep S3 URLs. No video URL changes unless the client specifically requests switching to Dropbox or reports broken S3 links.

---

## Verification

### Automated Tests
```bash
cd frontend && npx vitest run src/test/videoData.test.js src/test/BestPractices.test.jsx
```
- [ ] All 11 data integrity tests pass
- [ ] All 5 rendering tests pass

### Manual Test
```bash
# Rebuild and start containers
docker compose down && docker compose up -d --build

# Open in browser
open http://localhost:3000
```

### Expected Output

**Best Practices page (`/best-practices`):**
- [ ] Page heading reads "Best Practices Modeled" (not "Research-Backed Practices Modeled")
- [ ] Categories appear left-to-right: Idea Generation & Organization → Language Construction → Transcription
- [ ] Opening paragraph mentions all three composing processes
- [ ] Research paragraph says "early writing ability" (not "executive functioning")
- [ ] Bold terms read: idea generation & organization, language construction, transcription
- [ ] CTA text matches doc copy

**Navigation dropdown:**
- [ ] Labels read: Idea Generation & Organization, Language Construction, Transcription
- [ ] Order matches Best Practices page
- [ ] Links go to correct routes (`/idea-generation`, `/vocabulary-syntax`, `/handwriting-spelling`)

**Transcription page (`/handwriting-spelling`):**
- [ ] Page title reads "Transcription" (not "Handwriting & Spelling")
- [ ] Intro text renders as **two separate paragraphs** matching the doc
- [ ] 10 practice cards displayed (9 existing + Sequenced Segmentation)
- [ ] Sequenced Segmentation shows "coming soon" state (no video)
- [ ] Practice card order: Hold Pencil → Directionality → Phonemes → Sequenced Segmentation → Strokes → Compare Letters → Retrieve P-G → Apply P-G → Corrective Feedback → Invented Spelling
- [ ] Each practice description matches the doc's instructional phrasing
- [ ] All existing video links still work

**No regressions:**
- [ ] Vocabulary & Syntax page still loads at `/vocabulary-syntax`
- [ ] Idea Generation page still loads at `/idea-generation`
- [ ] Individual video pages still work for all categories
- [ ] No console errors

---

## References

- Source document: `docs/L4C Revision to Pages.docx`
- Related spec: `frontend/specs/001-feedback-updates/spec.md` (previous homepage updates)

---

## Spec Revisions

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2026-02-17 | Initial draft — all changes from L4C Revision document |
| 0.2 | 2026-02-17 | Added Change 1 (page heading); fixed Transcription description to two-element array |
| 0.3 | 2026-02-17 | Removed code templates — implementation agent should read live files via MCP |
| 0.4 | 2026-02-17 | Added unit tests — 11 data integrity tests + 5 rendering tests |
| 1.0 | 2026-02-17 | All components implemented — 16/16 tests passing, 0 regressions |
