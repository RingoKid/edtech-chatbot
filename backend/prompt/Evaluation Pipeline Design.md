# Evaluation Pipeline - Technical Specification

## Document Info

| Field        | Value                               |
| ------------ | ----------------------------------- |
| Project      | Language for Composing AI (L4C)     |
| Component    | Lesson Generation Evaluation System |
| Version      | 0.3 (Post v0.1 Implementation)      |
| Last Updated | 2026-01-12                          |

---

## Implementation Status

> **Current State:** v0.1 baseline implemented. Langfuse and evals are next.

| Component | Status | Notes |
|-----------|--------|-------|
| n8n lesson generator workflow | ✅ Implemented | `n8n/workflows/lesson-generator-v01.json` |
| Webhook trigger + validation | ✅ Implemented | `POST /webhook/generate` |
| OpenAI integration (HTTP Request) | ✅ Implemented | GPT-4o via direct API call |
| Form content (B, C, D, F) | ✅ Implemented | Hardcoded in Code node |
| n8n API wrapper script | ✅ Implemented | `n8n/api.sh` (secure credential handling) |
| Langfuse tracing | 🔲 Not started | Next priority |
| Langfuse scoring/evals | 🔲 Not started | After tracing |
| LLM-as-Judge | 🔲 Not started | After basic evals |
| Compositional prompt assembly | 🔲 Not started | Future iteration |
| Multi-model comparison | 🔲 Not started | Future iteration |
| eval.py CLI | 🔲 Not started | After Langfuse integration |

### Iteration Path

| Version | Focus | Status |
|---------|-------|--------|
| **v0.1** | Baseline single-shot generation | ✅ Done |
| **v0.2** | Add Langfuse tracing | 🔲 Next |
| **v0.3** | Add deterministic evals (Tier 1) | 🔲 Planned |
| **v0.4** | Add LLM-as-Judge evals (Tier 2) | 🔲 Planned |
| **v0.5** | Compositional prompt assembly | 🔲 Planned |
| **v0.6** | Multi-model comparison | 🔲 Planned |

---

## 1. Context & Background

### 1.1 Problem Statement

The L4C project generates scripted lesson plans for PreK-1st grade teachers. We need a systematic way to:

- Evaluate generated lesson quality against a gold standard (Form C)
- Compare different prompt engineering strategies
- Test multiple LLM providers (OpenAI, Anthropic)
- Iterate quickly without manual review
- Track quality metrics over time

### 1.2 Reference Materials

| Document          | Purpose                                | Token Estimate     |
| ----------------- | -------------------------------------- | ------------------ |
| Form B            | Structure rules, required explanations | ~800               |
| Form C            | Gold standard example output           | ~2,400             |
| Form D            | Scaffolded activities by section       | ~1,900             |
| Form F            | Sequence verbal cues (A-Z, a-z)        | ~650               |
| Form G            | Gestures for phonemes                  | ~500 (PDF)         |
| Form H            | Modification examples                  | ~850               |
| Georgia Standards | State standards by grade               | ~10,000 (PDF)      |
| **Total**         | All reference materials                | **~38,000 tokens** |

### 1.3 Success Criteria

| Metric                | Target                               |
| --------------------- | ------------------------------------ |
| Evaluation turnaround | < 2 minutes per test case            |
| Score reproducibility | Same input → same score (±2 points)  |
| Metric coverage       | 100% of Form B requirements captured |
| Model comparison      | Support 3+ providers simultaneously  |

---

## 2. Architectural Decisions

### 2.1 Technology Stack

| Layer                    | Tool                   | Status | Rationale                                                                |
| ------------------------ | ---------------------- | ------ | ------------------------------------------------------------------------ |
| **Prototyping**          | n8n (self-hosted)      | ✅ In use | Visual workflow builder, fast iteration |
| **Evaluation & Tracing** | Langfuse (self-hosted) | 🔲 Next | Open-source, offline + online eval, LLM-as-Judge, experiment tracking    |
| **Production**           | LangGraph              | 🔲 Future | Production-ready, proper state management, Python ecosystem              |
| **Vector Store**         | Pinecone / Chroma      | 🔲 Future | RAG retrieval experiments                                                |
| **CLI Automation**       | Python eval.py         | 🔲 Planned | Triggers n8n workflow, logs to Langfuse, prints results (no UI clicks)   |
| **LLM Providers**        | OpenAI                 | ✅ In use | GPT-4o via HTTP Request node |
| **LLM Providers**        | Anthropic              | 🔲 Planned | Claude Sonnet for model comparison |
| **API Access**           | n8n/api.sh wrapper     | ✅ In use | Secure credential handling for n8n REST API |

> **Design Philosophy (Target State):** Compositional prompt engineering — prompts assembled from reusable components. **Current State (v0.1):** Monolithic prompt with all forms hardcoded in Code node. Compositional assembly is a future iteration.

### 2.2 Key Decisions

**Decision 1: Prototype in n8n, Production in LangGraph**

- Rationale: n8n enables fast visual iteration for retrieval experiments; LangGraph provides production-grade agent infrastructure
- Trade-off: ~40-60% of n8n logic translates to LangGraph; some rework expected
- Alternative considered: Build directly in LangGraph
- Why rejected: Slower iteration; harder to visualize retrieval strategies

**Decision 2: Langfuse over Promptfoo**

- Rationale: Langfuse provides both offline AND online evaluation in one system; fully open-source and self-hostable; native LLM-as-Judge support; experiment history and comparison
- Trade-off: Langfuse has less polished model comparison UX than Promptfoo for pure offline iteration
- Alternative considered: Promptfoo (CLI-first, best offline eval) + Langfuse (online only)
- Why rejected: Two tools to maintain; shared rubrics still require coordination
- Key insight: Langfuse SDK allows scripted evaluation — we build `eval.py` to get CLI-like speed without manual dashboard clicking

**Decision 3: Self-hosted n8n and Langfuse**

- Rationale: Full control over data; no vendor lock-in; works offline; cost-effective at scale
- Trade-off: Must manage Docker infrastructure for both services
- Alternative considered: Cloud versions of both
- Why rejected: Data sovereignty concerns for educational content; cloud costs scale with usage

**Decision 4: Separate Judge Model**

- Rationale: Cross-model evaluation reduces bias (e.g., GPT-4 judging Claude output)
- Trade-off: Additional API cost for judge calls
- Configuration: Judge model configurable per evaluation run

**Decision 5: Compositional Prompt Engineering**

- Rationale: Prompts are not monolithic strings — they're composed from reusable parts (system roles, techniques, examples, formats). This enables systematic experimentation.
- Trade-off: More complex folder structure; requires assembly logic in n8n
- Alternative considered: Edit prompts as single files (standard approach)
- Why rejected: Cannot easily test "same prompt + different examples" or "same examples + different techniques"
- Key insight: First principles analysis revealed we're not just "editing prompts" — we're experimenting with prompt composition strategies. Standard tools treat prompts as atomic; our design treats them as composed systems.

---

## 3. System Architecture

### 3.0 Current Architecture (v0.1 — Implemented)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                     v0.1 LESSON GENERATOR (BASELINE)                    │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐          │
│  │ Webhook  │───►│    IF    │───►│   Code   │───►│   HTTP   │          │
│  │ Trigger  │    │ Validate │    │  Prompt  │    │ Request  │          │
│  │  POST    │    │ grade &  │    │ (Forms   │    │ (OpenAI) │          │
│  │/generate │    │ letter   │    │ hardcoded│    │  GPT-4o  │          │
│  └──────────┘    └────┬─────┘    └──────────┘    └────┬─────┘          │
│                       │                               │                 │
│                       ▼ (missing fields)              ▼                 │
│                 ┌──────────┐                   ┌──────────┐             │
│                 │ Respond  │                   │ Respond  │             │
│                 │  Error   │                   │ Success  │             │
│                 └──────────┘                   │ (lesson) │             │
│                                                └──────────┘             │
│                                                                         │
│  Files: n8n/workflows/lesson-generator-v01.json                         │
│  Test:  curl -X POST http://localhost:5678/webhook/generate             │
│         -d '{"grade": "PreK", "letter": "z"}'                           │
└─────────────────────────────────────────────────────────────────────────┘
```

**What v0.1 does NOT have:**
- No Langfuse tracing
- No evaluation/scoring
- No compositional prompt assembly
- No multi-model comparison
- Single hardcoded prompt with all forms embedded

---

### 3.1 Target Architecture (Full Vision)

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           EVALUATION SYSTEM                             │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                 PROMPT COMPONENTS (Text Files)                   │   │
│  │  ┌──────────┐  ┌──────────┐  ┌────────────┐  ┌───────────────┐  │   │
│  │  │ System   │  │Techniques│  │ Examples   │  │ Format/       │  │   │
│  │  │ Roles    │  │ (CoT,    │  │ (few-shot) │  │ Context       │  │   │
│  │  │ (v1,v2)  │  │ reflect) │  │            │  │               │  │   │
│  │  └──────────┘  └──────────┘  └────────────┘  └───────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │              EXPERIMENT CONFIGS (YAML)                           │   │
│  │  experiment-a.yaml: system-v2 + cot + few-shot-2                │   │
│  │  experiment-b.yaml: system-v1 + no-cot + zero-shot              │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                    n8n (Prompt Assembly)                         │   │
│  │  ┌──────────┐  ┌──────────────┐  ┌────────────┐  ┌───────────┐  │   │
│  │  │ Load     │─►│ Assemble     │─►│ Call LLMs  │─►│ Return    │  │   │
│  │  │ Config   │  │ Prompt       │  │ (parallel) │  │ Results   │  │   │
│  │  └──────────┘  └──────────────┘  └────────────┘  └───────────┘  │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│                              ▼                                          │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                  Langfuse (Eval & Tracing)                       │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐   │   │
│  │  │ Traces       │  │ LLM-as-Judge │  │ Experiment History   │   │   │
│  │  │ (full req)   │  │ (rubric      │  │ (compare configs     │   │   │
│  │  │              │  │  scoring)    │  │  over time)          │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                              │                                          │
│  ┌───────────────────────────┴─────────────────────────────────────┐   │
│  │                         CLI (eval.py)                            │   │
│  │   python eval.py --config experiment-a.yaml                      │   │
│  │   → Triggers n8n → Logs to Langfuse → Prints scores to terminal │   │
│  └─────────────────────────────────────────────────────────────────┘   │
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Data Flow

```
INPUT                    PROCESS                         OUTPUT
─────                    ───────                         ──────

experiment_config  ──►   1. Load Experiment Config ──►   Assembled Prompt
  (YAML file)            2. Load Components              (from parts)
test_case                3. Assemble Prompt                    │
  (grade, letter)        4. Inject Variables                   │
                                                               │
                                                               ▼
                         5. Call LLMs (parallel)   ──►   Generated Lessons
                            - GPT-4o                     (per model)
                            - Claude Sonnet                    │
                            - etc.                             │
                                                               ▼
                         6. Log to Langfuse        ──►   Traces with Metadata
                            - trace per model            - experiment name
                            - components used            - components used
                                                         - full I/O
                                                               │
                                                               ▼
                         7. LLM-as-Judge           ──►   Evaluation Scores
                            - rubric scoring             - scores by category
                            - cross-model judge          - pass/fail status
                                                               │
                                                               ▼
                         8. Print to Terminal      ──►   Instant Feedback
                         9. Store in Langfuse            + Historical Record
```

---

## 4. Evaluation Metrics Specification

### 4.1 Scoring System

| Category                 | Points  | Weight   | Assertion Types Used       |
| ------------------------ | ------- | -------- | -------------------------- |
| A. Structure Compliance  | 20      | 20%      | `contains`                 |
| B. Verbatim Explanations | 25      | 25%      | `contains` (exact match)   |
| C. Format Markers        | 20      | 20%      | `regex`                    |
| D. Content Accuracy      | 20      | 20%      | `javascript`, `llm-rubric` |
| E. Pedagogical Quality   | 15      | 15%      | `llm-rubric`               |
| **Total**                | **100** | **100%** |                            |

### 4.2 Category A: Structure Compliance

**Purpose:** Verify all required lesson sections are present.

| ID  | Check                           | Points | Assertion                      |
| --- | ------------------------------- | ------ | ------------------------------ |
| A1  | Standards section exists        | 2      | `contains: "Standards"`        |
| A2  | Objectives section exists       | 2      | `contains: "Objectives"`       |
| A3  | Materials section exists        | 2      | `contains: "Materials"`        |
| A4  | Review & Connect section        | 3      | `contains: "Review & Connect"` |
| A5  | Model, Explain & Engage section | 3      | `contains: "Model, Explain"`   |
| A6  | Guided Practice section         | 3      | `contains: "Guided Practice"`  |
| A7  | Application section             | 3      | `contains: "Application"`      |
| A8  | Wrap-Up section                 | 2      | `contains: "Wrap-Up"`          |

### 4.3 Category B: Verbatim Explanations

**Purpose:** Form B requires specific explanations quoted exactly in brackets.

| ID  | Section          | Required Text (partial)                                                                                                                                                       | Points |
| --- | ---------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------ |
| B1  | Review & Connect | "The purpose of this part of the lesson is to start with a quick review of previously learned sounds"                                                                         | 5      |
| B2  | Review Warning   | "Do not use sounds that have not been directly taught"                                                                                                                        | 2      |
| B3  | Model, Explain   | "The purpose of this part of the lesson is to connect a sound or sound patterns that you focused on during your reading block to writing its corresponding grapheme patterns" | 5      |
| B4  | Guided Practice  | "The purpose of this part of the lesson is to give children practice writing the letter while supporting proper pencil grip and correct sequence of stroke formation"         | 5      |
| B5  | Application      | "The purpose of this part of the lesson is to facilitate children's spelling of the letter or letter patterns when they hear the sound"                                       | 5      |
| B6  | Wrap-Up          | "The purpose of this part of the lesson is to remind students what they were focused on and provide praise for their accomplishments"                                         | 3      |

### 4.4 Category C: Format Markers

**Purpose:** Verify correct use of formatting conventions per Form B.

| ID  | Marker               | Regex Pattern                                                          | Points |
| --- | -------------------- | ---------------------------------------------------------------------- | ------ |
| C1  | Teacher Script       | `#\s*Teacher Script`                                                   | 3      |
| C2  | Explanation blocks   | `\[Explanation:`                                                       | 3      |
| C3  | Child Response       | `\([Cc]hildren`                                                        | 3      |
| C4  | Teacher Does         | `\{[Tt]eacher`                                                         | 3      |
| C5  | Gesture              | `\+\s*Gesture`                                                         | 3      |
| C6  | Sequence Verbal Cues | `##\s*Sequence Verbal Cues`                                            | 3      |
| C7  | Modification prompt  | `\*\s*Adaptation` OR `Let me know if you would like any modifications` | 2      |

### 4.5 Category D: Content Accuracy

**Purpose:** Verify content matches reference forms.

| ID  | Check                         | Implementation                                                                                        | Points |
| --- | ----------------------------- | ----------------------------------------------------------------------------------------------------- | ------ |
| D1  | Verbal cues for target letter | JavaScript: lookup Form F, check if cues present                                                      | 5      |
| D2  | Verbal cues exact match       | LLM-rubric: "Do the sequence verbal cues match Form F exactly?"                                       | 3      |
| D3  | Uses approved activities      | Contains any of: "Sound Spark", "Sound Hunt", "Trace & Say", "Magic Finger Write"                     | 4      |
| D4  | Activities match section      | LLM-rubric: "Are review activities in Review section, guided practice activities in Guided Practice?" | 4      |
| D5  | Standards code present        | Regex: `ELAGSE[KG12]`                                                                                 | 2      |
| D6  | Grade-appropriate standards   | LLM-rubric: "Do standards match the specified grade level?"                                           | 2      |

### 4.6 Category E: Pedagogical Quality

**Purpose:** LLM-as-Judge evaluates teaching effectiveness.

| ID  | Criterion             | Rubric Prompt                                                                         | Scale | Points |
| --- | --------------------- | ------------------------------------------------------------------------------------- | ----- | ------ |
| E1  | Scaffolding           | "Rate how well the lesson progresses from review → modeling → practice → application" | 1-3   | 3      |
| E2  | Grade appropriateness | "Rate if the language complexity matches {grade} level"                               | 1-3   | 3      |
| E3  | Script naturalness    | "Rate if a real teacher could naturally speak this script"                            | 1-3   | 3      |
| E4  | Student expectations  | "Rate if expected child responses are clear and realistic"                            | 1-3   | 3      |
| E5  | Structured literacy   | "Rate alignment with structured literacy and science of reading"                      | 1-3   | 3      |

---

## 5. Implementation Guide

### 5.1 Prerequisites

| Requirement    | Version | Purpose                                   |
| -------------- | ------- | ----------------------------------------- |
| Docker         | 20.10+  | Container runtime                         |
| Docker Compose | 2.0+    | Multi-container orchestration             |
| Python         | 3.10+   | eval.py CLI script, Langfuse SDK          |
| n8n            | 1.0+    | Workflow automation (self-hosted)         |
| Langfuse       | latest  | Evaluation & tracing (self-hosted)        |
| PostgreSQL     | 15+     | Langfuse data storage (bundled in Docker) |
| API Keys       | -       | OpenAI, Anthropic                         |

### 5.2 Directory Structure

#### Current Structure (v0.1 — Implemented)

```
edtech-chatbot/
├── docker-compose.yml              # All services (backend, n8n, dynamodb, frontend)
├── CLAUDE.md                       # Project instructions for Claude Code
│
├── backend/
│   ├── .env.local                  # API keys (gitignored)
│   ├── specs/
│   │   └── 007-n8n-lesson-generator/
│   │       └── spec.md             # v0.1 implementation spec
│   └── prompt/
│       ├── Evaluation Pipeline Design.md    # This document
│       └── Handwriting & Spelling (Transcription) AI Codes/
│           ├── FORM B-Codes for Lesson Parts Handwriting & Spelling.txt
│           ├── FORM C_ Example Handwriting & Spelling Lesson for Output .txt
│           └── Supplementary Forms/
│               ├── FORM D Scaffolded Activities .txt
│               └── Form F_ Sequence Verbal Cues.txt
│
├── n8n/
│   ├── api.sh                      # ✅ API wrapper script (secure credential handling)
│   ├── workflows/
│   │   └── lesson-generator-v01.json   # ✅ Exported n8n workflow
│   ├── experiments/
│   │   └── changelog.md            # Experiment tracking
│   └── outputs/
│       └── v01-prek-z.md           # Sample output
│
└── .claude/
    └── settings.local.json         # Claude Code permissions (blocks .env.local)
```

#### Target Structure (Future — Not Yet Implemented)

```
edtech-chatbot/
├── ... (current structure) ...
│
├── prompt-components/              # 🔲 PLANNED: Reusable prompt parts
│   ├── system/                     # Role definitions (v1-basic, v2-expert)
│   ├── techniques/                 # CoT, step-by-step, reflection
│   ├── examples/                   # Few-shot examples
│   └── context/                    # Cleaned form content
│
├── configs/                        # 🔲 PLANNED: Experiment configs (YAML)
│   └── experiment-a.yaml           # Component combinations
│
├── rubrics/                        # 🔲 PLANNED: LLM-as-Judge criteria
│   ├── structure.txt
│   └── pedagogical.txt
│
├── tests/
│   └── golden-dataset.yaml         # 🔲 PLANNED: Test cases
│
└── eval.py                         # 🔲 PLANNED: CLI automation
```

> **Current State:** Forms are hardcoded in n8n Code node. Future iterations will externalize them into `prompt-components/` for compositional assembly.

### 5.3 Step 1: Docker Environment Setup

**5.3.1 Create docker-compose.yml**

Services (3 containers):

- **n8n** (port 5678) — Workflow automation, prompt assembly
- **langfuse** (port 3000) — Evaluation UI and API
- **postgres** (port 5432) — Langfuse data storage

```yaml
# docker-compose.yml (simplified)
version: "3.8"
services:
  n8n:
    image: n8nio/n8n:latest
    ports: ["5678:5678"]
    volumes:
      - ./n8n-data:/home/node/.n8n
      - ./prompt-components:/data/components:ro
      - ./configs:/data/configs:ro
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY}
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}

  langfuse:
    image: langfuse/langfuse:latest
    ports: ["3000:3000"]
    environment:
      - DATABASE_URL=postgresql://postgres:postgres@db:5432/langfuse
      - NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
      - SALT=${SALT}
      - NEXTAUTH_URL=http://localhost:3000
    depends_on: [db]

  db:
    image: postgres:15
    environment:
      - POSTGRES_PASSWORD=postgres
      - POSTGRES_DB=langfuse
    volumes:
      - ./postgres-data:/var/lib/postgresql/data
```

**5.3.2 Create .env file**

Required variables:

- `OPENAI_API_KEY` — For lesson generation
- `ANTHROPIC_API_KEY` — For model comparison
- `NEXTAUTH_SECRET` — Langfuse auth (generate: `openssl rand -base64 32`)
- `SALT` — Langfuse encryption (generate: `openssl rand -base64 32`)

**5.3.3 Start Services**

```bash
docker-compose up -d

# Verify all containers running
docker-compose ps

# Access:
# - n8n:      http://localhost:5678
# - Langfuse: http://localhost:3000
```

**5.3.4 Initial Langfuse Setup**

1. Open http://localhost:3000
2. Create account (first user = admin)
3. Create project → "L4C Lesson Eval"
4. Settings → API Keys → Create new key
5. Save `public_key` and `secret_key` to .env

### 5.4 Step 2: Experiment Configuration

**5.4.1 Create Experiment Config (YAML)**

Each experiment specifies which components to combine:

```yaml
# configs/experiment-a.yaml
name: "expert-with-cot"
description: "Expert role + chain of thought + 2 examples"

components:
  system: "system/v2-expert.txt"
  technique: "techniques/chain-of-thought.txt"
  examples: "examples/few-shot-2.txt"
  format: "format/markdown.txt"
  context:
    - "context/form_b.txt"
    - "context/form_c.txt"

assembly_order:
  - system
  - context
  - examples
  - technique
  - user_input
  - format

models:
  - openai:gpt-4o
  - anthropic:claude-3-sonnet

parameters:
  temperature: 0.7
  max_tokens: 4000
```

**5.4.2 Define Models**

| Provider  | Model           | Temperature | Purpose                   |
| --------- | --------------- | ----------- | ------------------------- |
| OpenAI    | gpt-4o          | 0.7         | Primary generator         |
| OpenAI    | gpt-4o-mini     | 0.7         | Cost comparison           |
| Anthropic | claude-3-sonnet | 0.7         | Cross-provider comparison |

**5.4.3 Create Golden Dataset (Test Cases)**

```yaml
# tests/golden-dataset.yaml
- id: "TC001"
  input:
    grade: "PreK"
    letter: "z"
    objective: "letter sound and writing"
  criteria:
    - "Has all required sections (Standards, Objectives, Materials, etc.)"
    - "Contains verbatim Form B explanations in brackets"
    - "Uses correct verbal cues from Form F for letter z"
    - "Activities are age-appropriate for PreK"
  notes: "Baseline test - should match Form C gold standard"

- id: "TC002"
  input:
    grade: "Kindergarten"
    letter: "sh"
    objective: "digraph sound and writing"
  criteria:
    - "Correctly handles digraph (two letters, one sound)"
    - "Uses appropriate scaffolding for digraphs"
# ... more test cases
```

**5.4.4 Create Rubrics (LLM-as-Judge Criteria)**

```text
# rubrics/pedagogical.txt
Evaluate this lesson plan for pedagogical quality.

Score each criterion 1-3:
1. Scaffolding: Does it progress review → model → practice → apply?
2. Grade appropriateness: Is language complexity right for {grade}?
3. Script naturalness: Could a real teacher speak this naturally?
4. Student expectations: Are expected responses clear and realistic?

Return JSON: {"scaffolding": N, "grade_fit": N, "natural": N, "expectations": N}
```

### 5.5 Step 3: Prepare Context Files

**5.5.1 Copy Reference Forms**

Source: `Prompt Engineering/Handwriting & Spelling (Transcription) AI Codes/`

| Source File                  | Destination          |
| ---------------------------- | -------------------- |
| `FORM B-Codes...txt`         | `context/form_b.txt` |
| `FORM C_ Example...txt`      | `context/form_c.txt` |
| `FORM D Scaffolded...txt`    | `context/form_d.txt` |
| `Form F_ Sequence...txt`     | `context/form_f.txt` |
| `Form H_ Modification...txt` | `context/form_h.txt` |

**5.5.2 Create Letter Lookup Rubric**

File: `rubrics/verbal-cues.txt`

Purpose: LLM-as-Judge validates that correct verbal cues appear for the target letter.

```text
# rubrics/verbal-cues.txt
You are evaluating a lesson plan for letter "{letter}".

Reference verbal cues from Form F:
{form_f_content}

Check if the lesson plan contains the correct verbal cues for this letter.

Score:
- 1.0: Exact match to Form F cues
- 0.5: Partially correct or paraphrased
- 0.0: Missing or incorrect cues

Return JSON: {"verbal_cue_score": N, "found_cues": "...", "expected_cues": "..."}
```

### 5.6 Step 4: Create Prompt Components

**5.6.1 System Roles**

```text
# prompt-components/system/v1-basic.txt
You are a lesson plan generator for {grade} grade teachers.
Generate a scripted lesson plan for teaching the letter "{letter}".
```

```text
# prompt-components/system/v2-expert.txt
You are an expert curriculum designer specializing in structured literacy
and the science of reading. You create scripted lesson plans that follow
research-based practices for PreK-1st grade phonics instruction.
```

**5.6.2 Techniques**

```text
# prompt-components/techniques/chain-of-thought.txt
Before generating the lesson, think through:
1. What prior knowledge should students have?
2. What is the key learning objective?
3. How will you scaffold from simple to complex?
4. What common misconceptions might arise?

Then generate the complete lesson plan.
```

**5.6.3 Examples (Few-Shot)**

```text
# prompt-components/examples/few-shot-2.txt
Here are two example lesson plans that demonstrate the expected format:

[Example 1: Letter 'm' for PreK]
{form_c_content_m}

[Example 2: Letter 's' for Kindergarten]
{form_c_content_s}

Now generate a similar lesson plan for:
```

**5.6.4 Format Specifications**

```text
# prompt-components/format/structured.txt
Format your response with these exact sections and markers:
- ## Standards (with Georgia code ELAGSE...)
- ## Objectives
- ## Materials
- ## Review & Connect [Explanation: ...]
- ## Model, Explain & Engage [Explanation: ...]
- ## Guided Practice [Explanation: ...]
- ## Application [Explanation: ...]
- ## Wrap-Up [Explanation: ...]

Use these markers for interactions:
- # Teacher Script: (for teacher speech)
- (Children...) for expected student responses
- {Teacher...} for teacher actions
- + Gesture: for physical gestures
```

### 5.7 Step 5: n8n Workflow

#### 5.7.0 Current Workflow (v0.1 — Implemented)

**File:** `n8n/workflows/lesson-generator-v01.json`
**Webhook:** `POST http://localhost:5678/webhook/generate`

```
Webhook Trigger → IF Validate → Build Prompt → HTTP Request (OpenAI) → Respond
                       ↓
                 Respond Error
```

| Node | Type | Purpose |
|------|------|---------|
| Webhook Trigger | `n8n-nodes-base.webhook` | POST /webhook/generate |
| IF Validate | `n8n-nodes-base.if` | Check grade & letter exist |
| Build Prompt | `n8n-nodes-base.code` | Assemble prompt with hardcoded forms |
| HTTP Request | `n8n-nodes-base.httpRequest` | Call OpenAI API (GPT-4o) |
| Respond Success | `n8n-nodes-base.respondToWebhook` | Return lesson JSON |
| Respond Error | `n8n-nodes-base.respondToWebhook` | Return validation error |

**Test:**
```bash
curl -X POST http://localhost:5678/webhook/generate \
  -H "Content-Type: application/json" \
  -d '{"grade": "PreK", "letter": "z"}'
```

**API Management:**
```bash
# List workflows
./n8n/api.sh workflows

# Activate workflow
./n8n/api.sh workflows/{id}/activate -X POST
```

---

#### 5.7.1 Target Workflow (Full Vision — Not Implemented)

**5.7.1.1 Node 1: Webhook Trigger**

- Method: POST
- Path: `/assemble-and-eval`
- Body parameters: `config_name`, `test_case` (grade, letter, objective)

**5.7.2 Node 2: Load Experiment Config**

- Read YAML file from `/data/configs/{config_name}.yaml`
- Parse components list and assembly order

**5.7.3 Node 3: Load Components (Loop)**

For each component in config:

- Read text file from `/data/components/{path}`
- Store in variables

**5.7.4 Node 4: Assemble Prompt (Code Node)**

```javascript
// Concatenate components in assembly_order
let prompt = "";
for (const part of config.assembly_order) {
  if (part === "user_input") {
    prompt += `Generate a ${test.duration} lesson for ${test.grade} grade on "${test.letter}".\n`;
  } else {
    prompt += components[part] + "\n\n";
  }
}
return { assembled_prompt: prompt };
```

**5.7.5 Node 5: Split to Models**

Create parallel branches for each model in config.models

**5.7.6 Node 6: Call LLM (per branch)**

- OpenAI node or Anthropic node based on model
- Input: assembled_prompt
- Temperature and max_tokens from config

**5.7.7 Node 7: Log to Langfuse (HTTP Request)**

```json
POST http://langfuse:3000/api/public/generations
{
  "traceId": "{{$json.trace_id}}",
  "name": "lesson-generation",
  "model": "{{$json.model}}",
  "input": "{{$json.assembled_prompt}}",
  "output": "{{$json.lesson_output}}",
  "metadata": {
    "experiment": "{{config.name}}",
    "components": "{{config.components}}",
    "test_case": "{{test_case.id}}"
  }
}
```

**5.7.8 Node 8: Run LLM-as-Judge (LLM Node)**

- Load rubric files
- Call judge model (GPT-4) with lesson output + rubric
- Parse JSON scores

**5.7.9 Node 9: Log Scores to Langfuse**

```json
POST http://langfuse:3000/api/public/scores
{
  "traceId": "{{$json.trace_id}}",
  "name": "structure_compliance",
  "value": 0.92
}
```

**5.7.10 Node 10: Return Results**

Aggregate scores and return to CLI caller.

### 5.8 Step 6: Create CLI Automation (eval.py)

**5.8.1 The eval.py Script**

```python
# eval.py
import requests
import yaml
import sys

N8N_WEBHOOK = "http://localhost:5678/webhook/assemble-and-eval"

def run_experiment(config_name):
    with open(f"tests/golden-dataset.yaml") as f:
        tests = yaml.safe_load(f)

    print(f"\n🧪 EXPERIMENT: {config_name}")
    print("="*60)

    for test in tests:
        response = requests.post(N8N_WEBHOOK, json={
            "config_name": config_name,
            "test_case": test
        })
        results = response.json()

        print(f"\n📝 Test: {test['id']}")
        for model, scores in results['models'].items():
            print(f"   🤖 {model}: {scores['overall']:.2f}")

if __name__ == "__main__":
    config = sys.argv[1] if len(sys.argv) > 1 else "experiment-a"
    run_experiment(config)
```

**5.8.2 Usage**

```bash
# Run specific experiment
python eval.py experiment-a

# Compare experiments
python eval.py experiment-a
python eval.py experiment-b
# Check Langfuse dashboard for side-by-side comparison
```

### 5.9 Step 7: Validate Setup

**5.9.1 Baseline Test**

Run Form C (gold standard) through pipeline. Expected: High scores across all rubrics.

**5.9.2 Negative Test**

Submit intentionally bad lesson. Expected: Low scores, easy to diagnose in Langfuse traces.

**5.9.3 Experiment Comparison**

Run same test cases with different experiment configs. Compare in Langfuse.

---

## 6. Retrieval Strategy Experiments

### 6.1 Experiment Matrix

| ID    | Strategy            | Context Loaded             | Hypothesis                      |
| ----- | ------------------- | -------------------------- | ------------------------------- |
| EXP-1 | Full Context        | All forms (~38k tokens)    | Best quality, highest cost      |
| EXP-2 | Minimal             | Form B only                | Baseline, likely low quality    |
| EXP-3 | Structure + Example | Form B + Form C            | Good balance                    |
| EXP-4 | RAG                 | Vector search top-k chunks | Efficient, may miss context     |
| EXP-5 | LLM Routing         | LLM selects needed forms   | Smart selection, extra LLM call |

### 6.2 Experiment Protocol

1. Run each strategy against all test cases (TC001-TC006)
2. Use same model (GPT-4o) for generation
3. Record scores for each category
4. Calculate average scores per strategy
5. Compare cost (token usage) vs. quality trade-off

### 6.3 Success Metrics

| Strategy             | Pass Threshold  | Target Avg Score |
| -------------------- | --------------- | ---------------- |
| Production candidate | 90% pass rate   | ≥ 85/100         |
| Acceptable           | 75% pass rate   | ≥ 75/100         |
| Needs work           | < 75% pass rate | < 75/100         |

---

## 7. Results Schema

### 7.1 Langfuse Data Model

**Traces** (one per evaluation run):

| Field               | Type     | Description                |
| ------------------- | -------- | -------------------------- |
| id                  | string   | Unique trace ID            |
| name                | string   | "experiment-a/TC001"       |
| timestamp           | datetime | When evaluation ran        |
| metadata.experiment | string   | Experiment config name     |
| metadata.components | object   | Which components were used |
| metadata.test_case  | string   | Test case ID               |

**Generations** (nested under trace):

| Field   | Type   | Description                  |
| ------- | ------ | ---------------------------- |
| model   | string | gpt-4o, claude-sonnet, etc.  |
| input   | string | Assembled prompt (full text) |
| output  | string | Generated lesson plan        |
| tokens  | number | Token usage                  |
| latency | number | Response time (ms)           |

**Scores** (attached to trace):

| Score Name            | Type | Description      |
| --------------------- | ---- | ---------------- |
| structure_compliance  | 0-1  | Category A       |
| verbatim_explanations | 0-1  | Category B       |
| format_markers        | 0-1  | Category C       |
| content_accuracy      | 0-1  | Category D       |
| pedagogical_quality   | 0-1  | Category E       |
| overall               | 0-1  | Weighted average |

**Queryable via Langfuse UI:**

- Filter by experiment name
- Compare scores across models
- View trends over time
- Drill into individual traces for debugging

---

## 8. Migration to Production

### 8.1 LangGraph Implementation

After prototyping validates the best prompt composition strategy:

| n8n Component   | LangGraph Equivalent           |
| --------------- | ------------------------------ |
| Webhook trigger | FastAPI endpoint               |
| Load config     | Python dict/YAML loader        |
| Load components | File I/O functions             |
| Assemble prompt | Python string builder          |
| LLM node        | `ChatOpenAI` / `ChatAnthropic` |
| Switch node     | Conditional edges in graph     |
| Log to Langfuse | Langfuse callback handler      |

### 8.2 What Transfers Directly

| Asset              | Transfer Method              |
| ------------------ | ---------------------------- |
| Prompt components  | Copy text files as-is        |
| Experiment configs | YAML files unchanged         |
| Golden dataset     | YAML files unchanged         |
| Rubrics            | Text files unchanged         |
| Langfuse project   | Same instance, same API keys |
| Evaluation history | Already in Langfuse          |

### 8.3 What Needs Rewrite

| Component      | Effort | Notes                      |
| -------------- | ------ | -------------------------- |
| Assembly logic | Low    | Python function, ~30 lines |
| Orchestration  | Medium | LangGraph state machine    |
| Error handling | Medium | Proper try/except, retries |
| API layer      | Medium | FastAPI endpoints          |

### 8.4 LangGraph Example

```python
from langgraph.graph import StateGraph
from langfuse.callback import CallbackHandler

langfuse_handler = CallbackHandler(
    public_key="pk-lf-...",
    secret_key="sk-lf-...",
    host="http://localhost:3000"
)

class LessonState(TypedDict):
    config: dict
    components: dict
    assembled_prompt: str
    outputs: dict[str, str]  # model -> output
    scores: dict[str, float]

def load_components(state):
    # Same logic as n8n, now in Python
    ...

def assemble_prompt(state):
    # Same logic as n8n Code node
    ...

def generate_lesson(state):
    # Call LLM with Langfuse callback
    ...

graph = StateGraph(LessonState)
graph.add_node("load", load_components)
graph.add_node("assemble", assemble_prompt)
graph.add_node("generate", generate_lesson)
graph.add_edge("load", "assemble")
graph.add_edge("assemble", "generate")

app = graph.compile()
```

### 8.5 Continuity with Langfuse

**Key advantage:** Langfuse spans both prototype and production.

- Development traces: Tagged with `env: dev`
- Production traces: Tagged with `env: prod`
- Same dashboard, same scoring, continuous history
- No data migration needed

---

## 9. Appendix

### 9.1 Form F Reference (Verbal Cues)

Uppercase:

- A: Big line up, big line down, little line across
- B: Big line down, rainbow bump, rainbow bump
- Z: Little line across. Slant down the stairs. Little line across
- (See form_f.txt for complete list)

Lowercase:

- a: Start at the middle, rainbow around, little line down
- b: Big line down, rainbow bump from the middle
- z: Little line across, slant down the stairs, little line across
- (See form_f.txt for complete list)

### 9.2 Form D Reference (Activities by Section)

**Review & Connect:**

- Sound Spark (low-level)
- Tap that Sound (low-level)
- Sound Detective (middle-level)
- Write the Sound (high-level)

**Model, Explain & Engage:**

- Sound Hunt (low-level)
- Hide-and-Seek Sound (middle-level)
- Sound Puzzle (high-level)

**Guided Practice:**

- Magic Finger Write (low-level)
- Trace & Say (middle-level)
- Cover & Try (high-level)

**Application:**

- Write the Sound You Hear (low-level)
- Sound-Letter Hunt (middle-level)
- Mystery Word Builder (middle-level)

### 9.3 Related Documents

- [[Dropbox Reference Materials]] - Complete form index
- [[LLM Production Evaluation Strategies]] - 2025 evaluation landscape analysis
- Form B - Structure specification
- Form C - Gold standard output
- Form D - Activity catalog
- Form F - Verbal cues lookup
- Form H - Modification patterns

---

## 10. Revision History

| Version | Date       | Changes |
| ------- | ---------- | ------- |
| 0.1     | 2025-01-05 | Initial draft with Promptfoo architecture |
| 0.2     | 2026-01-10 | Major revision: Replaced Promptfoo with Langfuse; Added compositional prompt engineering design |
| 0.3     | 2026-01-12 | **Post-implementation update:** Added Implementation Status section; Documented v0.1 baseline; Updated architecture diagrams to show current vs target state; Updated directory structure to match actual project; Added API wrapper script documentation |

### Key Changes in v0.3

1. **Implementation Status Added**
   - Clear tracking of what's implemented vs planned
   - Iteration path with version milestones

2. **Architecture Documentation Updated**
   - Added Section 3.0: Current Architecture (v0.1)
   - Renamed Section 3.1 to "Target Architecture"
   - Clear distinction between implemented and planned

3. **Directory Structure Updated**
   - Reflects actual project structure
   - Shows current files vs planned directories
   - Documents `n8n/api.sh` wrapper script

4. **n8n Workflow Section Updated**
   - Added Section 5.7.0: Current Workflow (v0.1)
   - Documents actual nodes and test commands
   - Shows API management commands

5. **What's Actually Implemented (v0.1)**
   - Simple webhook → validate → prompt → OpenAI → respond
   - Forms hardcoded in Code node
   - Single model (GPT-4o)
   - API wrapper script for secure credential handling

### Key Changes in v0.2

1. **Evaluation Engine:** Promptfoo → Langfuse (self-hosted)
   - Rationale: Single tool for offline + online evaluation
   - Benefit: Continuous history from dev to production

2. **Prompt Architecture:** Monolithic → Compositional
   - Prompts assembled from reusable components
   - Experiments defined as YAML configs
   - Enables systematic A/B testing of prompt strategies

3. **Workflow:** Manual iteration → CLI automation
   - eval.py script triggers full pipeline
   - Results printed to terminal + logged to Langfuse
   - Fast iteration without UI clicking

4. **Design Philosophy:** Tool-first → First principles
   - Started from requirements, not from tool features
   - Discovered that "prompt editing" was actually "prompt composition"
   - Designed custom architecture to match actual workflow
