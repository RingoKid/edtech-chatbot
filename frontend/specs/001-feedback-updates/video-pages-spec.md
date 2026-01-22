# Spec 001b: Video Pages Implementation

## Overview

Implement individual video pages for three practice categories using videos hosted on AWS S3, displayed via React Player.

**Use Context7** to get latest docs for `react-player`, `react-router-dom`, and `framer-motion`.

## Implementation Status

| Component | Status | Notes |
|-----------|--------|-------|
| **Phase 1: AWS Infrastructure** | | |
| S3 bucket + video upload | ✅ Done | `l4c-videos` bucket, 40 videos uploaded |
| **Phase 2: Frontend** | | |
| Add `react-player` to package.json | ✅ Done | v3.4.0 |
| Create `videoData.js` | ✅ Done | `src/data/videoData.js` |
| Create `VideoPageTemplate` component | ✅ Done | `src/components/VideoPageTemplate.jsx` |
| Update category pages | ✅ Done | All 3 category pages updated |
| Update BestPractices.jsx routes | ✅ Done | Fixed `/vocabulary-syntax` and `/idea-generation` |
| Add routes in AppRoutes.jsx | ✅ Done | Dynamic routing with `:videoId` param |

---

## Phase 1: AWS Infrastructure

### 1.1 Create S3 Bucket and Upload Videos

Source: `/Users/bdi-lab/Dropbox/Wixsite Videos/`

```bash
# Create bucket
aws s3 mb s3://l4c-videos --region us-east-1

# Enable public access
aws s3api put-public-access-block \
  --bucket l4c-videos \
  --public-access-block-configuration \
  "BlockPublicAcls=false,IgnorePublicAcls=false,BlockPublicPolicy=false,RestrictPublicBuckets=false"

# Set public read policy
aws s3api put-bucket-policy --bucket l4c-videos --policy '{
  "Version": "2012-10-17",
  "Statement": [{
    "Sid": "PublicReadGetObject",
    "Effect": "Allow",
    "Principal": "*",
    "Action": "s3:GetObject",
    "Resource": "arn:aws:s3:::l4c-videos/*"
  }]
}'

# Enable CORS
aws s3api put-bucket-cors --bucket l4c-videos --cors-configuration '{
  "CORSRules": [{
    "AllowedOrigins": ["*"],
    "AllowedMethods": ["GET", "HEAD"],
    "AllowedHeaders": ["*"],
    "MaxAgeSeconds": 3600
  }]
}'

# Upload videos
aws s3 sync "/Users/bdi-lab/Dropbox/Wixsite Videos/" s3://l4c-videos/videos/ \
  --content-type "video/mp4"

# Verify
aws s3 ls s3://l4c-videos/videos/
```

**Video Base URL:** `https://l4c-videos.s3.amazonaws.com/videos/`

---

## Phase 2: Video Mapping

### TRANSCRIPTION (Handwriting & Spelling) - 9 Practices

| Page Title | Route Slug | Video File(s) |
|-----------|------------|---------------|
| Hold Pencil Correctly | `hold-pencil-correctly` | `hold pen 2.mp4`, `Hold Pencil2.mp4` |
| Directionality | `directionality` | `Directionality Left to Right.mp4`, `Directionality 2 (1).mp4` |
| Pronounce, Identify, & Isolate Phonemes | `pronounce-identify-isolate-phonemes` | `Correct Pronunciation.mp4`, `sound iso.mp4` |
| Correct Letter Sequence of Strokes | `correct-letter-sequence-strokes` | `strokes.mp4`, `Sequence of Strokes.mp4` |
| Compare and Contrast Letter Forms | `compare-contrast-letter-forms` | `comp graph.mp4` |
| Retrieve and Connect Phoneme-Grapheme Patterns | `retrieve-connect-phoneme-grapheme` | `Review Phoneme-Grapheme (1).mp4` |
| Apply Phoneme Grapheme Patterns | `apply-phoneme-grapheme-patterns` | `phoneme grapgheme pattern.mp4` |
| Corrective Feedback | `corrective-feedback` | `corrective feedback.mp4` |
| Encourage Invented Spelling | `encourage-invented-spelling` | `Encourage Invented Spelling.mp4` |

**Category route:** `/handwriting-spelling`
**Category description:** These practices help children strengthen their recall of sound–letter correspondences and develop the skills to segment spoken words into individual phonemes.

---

### LANGUAGE CONSTRUCTION (Vocabulary & Syntax) - 5 Practices

| Page Title | Route Slug | Video File(s) |
|-----------|------------|---------------|
| Embed Vocabulary into Sentence Generation | `embed-vocabulary-sentence-generation` | `Retrieve Vocabulary in Sentence Building.mp4`, `Retrieve Vocabulary 2.mp4` |
| Build Vocabulary Depth to Support Word Choice | `build-vocabulary-depth-word-choice` | `Categorize Words.mp4`, `Word Choice.mp4` |
| Connecting Words | `connecting-words` | **NO VIDEO YET** |
| Build Sentence Awareness | `build-sentence-awareness` | `Sentence Structure Nouns and Verbs.mp4` |
| Build Sentence Manipulation | `build-sentence-manipulation` | `Build Sentence Manipulation.mp4` |

**Category route:** `/vocabulary-syntax`
**Category description:** These practices help children develop syntax, vocabulary, and morphology, enabling them to build language more fluidly.

---

### IDEA GENERATION & ORGANIZATION - 9 Practices

| Page Title | Route Slug | Video File(s) |
|-----------|------------|---------------|
| Define Topic & Purpose | `define-topic-purpose` | `Define Topic & Purpose.mp4` |
| Features of Genre | `features-of-genre` | `relevant details.mp4`, `Fact vs Fantasy.mp4` |
| Recall Information Related to a Topic | `recall-information-topic` | `writing be4 drawing.mp4` |
| Connect to Unit Concepts | `connect-unit-concepts` | `Connect to Unit Topics.mp4` |
| Model & Support Application of Genre Features | `model-support-genre-features` | **NO VIDEO YET** |
| Draw Together Cueing Content | `draw-together-cueing-content` | `writing be4 drawing.mp4`, `dbe4 write 2.mp4` |
| Oral Rehearsal of Ideas | `oral-rehearsal-ideas` | `Oral Rehearsal.mp4` |
| Question to Cue Elaboration | `question-cue-elaboration` | `using qs.mp4` |
| Revise to Apply Linguistic & Structural Features | `revise-linguistic-structural-features` | `Fact vs Fantasy.mp4` |

**Category route:** `/idea-generation`
**Category description:** These practices help children recall concepts and understand genre features, supporting them in developing and organizing ideas effectively.

---

## Phase 3: Frontend Implementation

### 3.1 Add Dependency

Add `react-player` (v3.4.0+) to `frontend/package.json`, then rebuild containers.

### 3.2 Create Video Data Config

Create `frontend/src/data/videoData.js`:
- Export arrays: `transcriptionVideos`, `languageConstructionVideos`, `ideaGenerationVideos`
- Each video object: `{ id, title, practiceTitle, description, videos: [{ url, label }], noVideoYet? }`
- Helper: `getVideoById(id)` - returns video object
- Helper: `getRelatedVideos(id, category, limit)` - returns related videos excluding current
- Use `encodeURIComponent()` for filenames with spaces in URLs

### 3.3 Create VideoPageTemplate Component

Create `frontend/src/components/VideoPageTemplate.jsx`:
- Props: `video`, `category`, `categoryTitle`, `backLink`, `relatedVideos`
- Features:
  - Back navigation link
  - Video title and practice description
  - ReactPlayer with controls (use `src` prop, not `url` - v3.x API)
  - Video selector buttons when multiple videos exist
  - "Video coming soon" placeholder when `noVideoYet: true`
  - "Explore More" section showing related videos
- Use existing styling patterns (Tailwind, framer-motion)

### 3.4 Update Category Pages

Update `HandwritingSpelling.jsx`, `VocabularySyntax.jsx`, `IdeaGeneration.jsx`:
- Import video data from `videoData.js`
- Link each practice card to its individual page route

### 3.5 Update BestPractices.jsx

Fix route links:
- Vocabulary: `/vocabulary-syntax` (was `/videos/vocabulary`)
- Idea Generation: `/idea-generation` (was `/videos/idea-generation`)

### 3.6 Add Routes

Add 23 individual video page routes to `AppRoutes.jsx`:
- Pattern: `/<category>/<slug>` → renders `VideoPageTemplate` with video data
- Can use dynamic routing or individual page components

---

## Notes

- **2 practices have NO VIDEO YET:** "Connecting Words" and "Model & Support Application of Genre Features"
- **Shared videos:** `writing be4 drawing.mp4` and `Fact vs Fantasy.mp4` are used in multiple pages

---

## Verification

```bash
# AWS - check videos uploaded
aws s3 ls s3://l4c-videos/videos/ --human-readable
curl -I "https://l4c-videos.s3.amazonaws.com/videos/Oral%20Rehearsal.mp4"
```

**Frontend** - After rebuild, verify at http://localhost:3000:
- [ ] All 23 video pages load
- [ ] Videos play from S3
- [ ] Multi-video pages show selector buttons
- [ ] "No Video Yet" pages show placeholder
- [ ] "Explore More" shows related videos

---

## Implementation Files

| File | Purpose |
|------|---------|
| `frontend/src/data/videoData.js` | Central video configuration with S3 URLs |
| `frontend/src/components/VideoPageTemplate.jsx` | Reusable video page component |
| `frontend/src/pages/HandwritingSpelling.jsx` | Category listing page (updated) |
| `frontend/src/pages/VocabularySyntax.jsx` | Category listing page (updated) |
| `frontend/src/pages/IdeaGeneration.jsx` | Category listing page (updated) |
| `frontend/src/pages/BestPractices.jsx` | Fixed route links |
| `frontend/src/AppRoutes.jsx` | Dynamic routing for video pages |

---

## References

- Feedback source: `frontend/specs/001-feedback-updates/feedbacks/individual-pages-transcription.md`
- Video source: `/Users/bdi-lab/Dropbox/Wixsite Videos/`

---

## Spec Revisions

| Version | Date | Changes |
|---------|------|---------|
| 0.1 | 2025-01-22 | Initial spec |
| 0.2 | 2025-01-22 | Simplified - removed verbose code, kept intent + data |
| 0.3 | 2026-01-22 | Implementation complete - AWS S3 + Frontend |
