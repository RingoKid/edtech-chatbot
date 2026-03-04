# Feature Specifications

This directory contains all feature specifications, implementation reviews, incident resolutions, and architectural decisions for the EdTech Chatbot backend.

## Structure

Each feature is organized in its own numbered folder:

```
specs/
├── 001-auth-jwt-system/
│   ├── spec.md                    # Feature specification
│   ├── reviews/                   # Implementation reviews
│   │   └── 001-implementation.md
│   ├── incidents/                 # Issues encountered and resolved
│   │   └── 001-bcrypt-issue.md
│   └── decisions/                 # Architecture decisions for this feature
│
├── 002-lesson-graph/
│   ├── 001-greeting-main-router.md
│   ├── 002-main-router-clarification-loop.md
│   ├── 003-dynamic-parameter-collection.md
│   ├── 004-expand-handwriting-parameters.md
│   └── 005-expand-vocab-idea-gen-parameters.md
│
└── README.md (this file)
```

## Features

### 001 - JWT Authentication System
**Status:** Implemented
**Spec:** [001-auth-jwt-system/spec.md](./001-auth-jwt-system/spec.md)
**Description:** JWT-based authentication with refresh tokens, role-based access control, and session management using DynamoDB.

**Reviews:**
- [001-implementation.md](./001-auth-jwt-system/reviews/001-implementation.md) - Post-implementation review (Grade: A-, 9/10)

**Incidents:**
- [001-bcrypt-issue.md](./001-auth-jwt-system/incidents/001-bcrypt-issue.md) - Bcrypt compatibility issue with passlib

**Decisions:**
- _(None yet)_

### 002 - Lesson Planning Graph
**Status:** Implemented
**Specs:** [002-lesson-graph/](./002-lesson-graph/)
**Description:** LangGraph-based conversation flow for lesson planning with greeting, routing, and parameter collection.

**Sub-specs:**
- [001-greeting-main-router.md](./002-lesson-graph/001-greeting-main-router.md) - Initial greeting and task routing
- [002-main-router-clarification-loop.md](./002-lesson-graph/002-main-router-clarification-loop.md) - Clarification loop for ambiguous input
- [003-dynamic-parameter-collection.md](./002-lesson-graph/003-dynamic-parameter-collection.md) - Dynamic parameter collection system
- [004-expand-handwriting-parameters.md](./002-lesson-graph/004-expand-handwriting-parameters.md) - Handwriting task parameters
- [005-expand-vocab-idea-gen-parameters.md](./002-lesson-graph/005-expand-vocab-idea-gen-parameters.md) - Vocabulary and idea generation parameters

### 006 - Chat History System
**Status:** Implemented
**Spec:** [006-chat-history-system/spec.md](./006-chat-history-system/spec.md)
**Description:** DynamoDB-based chat history with conversation persistence and retrieval APIs.

### 007 - n8n Lesson Generator Workflow
**Status:** Removed
**Description:** ~~n8n workflow for generating handwriting & spelling lesson plans.~~ Superseded by the LangGraph-based handwriting generator (spec 013). n8n service and workflows have been removed from the project.

### 008 - Langfuse Evaluation System
**Status:** Implemented (v0.1)
**Spec:** [008-langfuse-evals/spec.md](./008-langfuse-evals/spec.md)
**Description:** Backend APIs for running prompts against multiple models and evaluating outputs. Uses Langfuse Cloud for experiment tracking and cost calculation.

**Features:**
- Multi-model comparison (OpenAI GPT + Google Gemini)
- Rule-based evaluation criteria (structure_complete)
- Langfuse tracing and scoring
- Dataset management for experiment tracking

**Related Files:**
- `app/llm/` - Shared LLM infrastructure
- `app/langfuse/` - Evaluation module

### 009 - Architecture v2
**Status:** Proposal
**Spec:** [009-architecture-v2/proposal.md](./009-architecture-v2/proposal.md)
**Description:** Redesigned architecture using ReAct agents and Langfuse prompt management.

### 010 - Greeting & Routing Agent
**Status:** Implemented
**Spec:** [010-routing-agent/spec.md](./010-routing-agent/spec.md)
**Description:** ReAct agent that handles initial greeting and routes users to task-specific agents using tool calls. First implementation of the v2 architecture.

**Features:**
- ReAct agent with `create_react_agent` from LangGraph
- Three routing tools (handwriting, vocabulary, idea_generation)
- Placeholder nodes for future task agents
- Langfuse prompt management integration
- Evaluation tests with 90%+ routing accuracy

**Related Files:**
- `app/graph/agents/routing.py` - Routing agent definition
- `app/graph/nodes/placeholders.py` - Task placeholder nodes
- `tests/evals/test_routing_agent.py` - Eval tests
- `tests/datasets/routing_agent.py` - Test dataset

### 011 - Parameter Collection Agent
**Status:** Implemented
**Spec:** [011-param-agent/spec.md](./011-param-agent/spec.md)
**Description:** ReAct agent that collects task-specific parameters through conversation. First task type implemented: handwriting.

**Features:**
- Single param agent with task-specific tools (handwriting first)
- `submit_handwriting_params(grade, letter, student_level)` tool
- Parameter extraction from tool calls in node wrapper
- Generator placeholder showing collected params
- Evaluation tests with 85%+ param extraction accuracy

**Related Files:**
- `app/graph/agents/param.py` - Param agent and handwriting tool
- `app/graph/state.py` - `HandwritingParams` TypedDict
- `app/graph/graph.py` - Param agent node and extraction logic
- `app/graph/nodes/placeholders.py` - Generator placeholder
- `tests/evals/test_param_agent.py` - Eval tests
- `tests/datasets/param_agent.py` - Test dataset (18 cases)

### 012 - Vocabulary & Idea Generation Parameter Tools
**Status:** Implemented
**Spec:** [012-vocab-idea-params/spec.md](./012-vocab-idea-params/spec.md)
**Description:** Extends the param agent with vocabulary and idea generation tools. Adds two new parameter collection flows to complete the Layer 2 task agents.

**Features:**
- `submit_vocabulary_params(grade, writing_type, key_vocabulary, objectives, student_level)` tool
- `submit_idea_generation_params(grade, genre, genre_component, writing_stage, objectives, student_level)` tool
- Updated routing: vocab and idea_generation now go to param_agent
- Generator placeholders showing collected params
- Evaluation tests for both new param types

**Related Files:**
- `app/graph/agents/param.py` - All three param tools
- `app/graph/state.py` - VocabularySyntaxParams, IdeaGenerationParams TypedDicts
- `app/graph/graph.py` - Extraction functions for all param types
- `app/graph/nodes/placeholders.py` - Generator placeholders
- `tests/evals/test_vocab_params.py` - Vocab eval tests
- `tests/evals/test_idea_params.py` - Idea generation eval tests
- `tests/datasets/vocab_params.py` - Vocab test dataset (18 cases)
- `tests/datasets/idea_params.py` - Idea generation test dataset (20 cases)

### 013 - Handwriting Generator Agent
**Status:** Implemented
**Spec:** [013-handwriting-generator/spec.md](./013-handwriting-generator/spec.md)
**Description:** ReAct agent that generates handwriting & spelling lesson plans following the L4C methodology. Replaces the handwriting generator placeholder with a real lesson generator.

**Features:**
- ReAct agent with `create_agent` from `langchain.agents`
- `finalize_lesson()` tool to signal completion
- Reference materials loaded from `handwriting_reference.md` (Forms B, C, D, F, H)
- Langfuse prompt management with `handwriting-generator` prompt
- Lesson structure following L4C methodology (Standards, Objectives, Materials, D.1-5)
- Verbatim explanations from Form B
- Verbal cues from Form F for each letter
- Activity level selection based on student_level (low/mid/high from Form D)
- Multi-turn conversation for modifications
- Rule-based evaluation criteria (structure_complete, verbatim_check, verbal_cues_correct)

**Related Files:**
- `app/graph/agents/handwriting_generator.py` - Generator agent and finalize tool
- `app/graph/state.py` - `lesson_finalized` state field
- `app/graph/graph.py` - Generator node, routing logic
- `app/langfuse/criteria.py` - Eval criteria functions
- `prompt/reference_materials/handwriting_reference.md` - L4C reference materials
- `scripts/setup_prompts.py` - Langfuse prompt setup
- `tests/evals/test_handwriting_generator.py` - Eval tests (10/11 passed)
- `tests/datasets/handwriting_generator.py` - Test dataset (14 cases)

### 014 - LLM Judge Evals — Scaffolding Sequencing
**Status:** Implemented
**Spec:** [014-llm-judge-evals/spec.md](./014-llm-judge-evals/spec.md)
**Description:** LLM judge evaluations for scaffolding sequencing quality. Uses gpt-5.2 as judge model to assess whether generated handwriting lessons sequence activities logically within and across sections.

**Features:**
- Pre-generated lesson fixtures (12 param combos) for fast, deterministic eval runs
- Within-section judge: activities ordered easier → harder within each section
- Across-section judge: later sections build on skills from earlier sections
- Structured output via Pydantic models for deterministic score computation
- Markdown report with summary table + per-fixture pair-level detail with judge reasoning
- Configurable judge model via `--model` flag

**Related Files:**
- `scripts/generate_eval_fixtures.py` - Fixture generation (runs full graph)
- `scripts/run_scaffolding_evals.py` - Eval runner (judge calls + report)
- `tests/evals/models.py` - Pydantic models for structured judge output
- `tests/evals/rubrics/scaffolding_within_activity.md` - Within-section judge prompt
- `tests/evals/rubrics/scaffolding_between_activity.md` - Across-section judge prompt
- `app/langfuse/criteria.py` - Registry entries for both criteria

**Decisions:**
- [001-decoupled-fixtures.md](./014-llm-judge-evals/decisions/001-decoupled-fixtures.md) - Why fixtures are pre-generated rather than live

### 015 - Scaffolding Evals Phase 2 — Gradual Release & Decomposition
**Status:** Implemented
**Spec:** [015-scaffolding-evals-phase-2/spec.md](./015-scaffolding-evals-phase-2/spec.md)
**Description:** Two new LLM judge evals for rubric criterion 2: gradual release of teacher support and decomposition of complex tasks into sub-skills. Extends the scaffolding eval suite from 2 to 4 evals.

**Features:**
- Gradual release eval: checks if teacher support decreases across sections (I do → We do → You do) and within Section 3
- Decomposition eval: checks if complex tasks in Sections 3-4 have prerequisite sub-skills taught in earlier sections
- Cognitive load trade-off handling in gradual release judge
- Extended summary table with 4 eval columns + averages
- Per-fixture detail with support level tables, transition tables, and component skill tables

**Related Files:**
- `tests/evals/models.py` - 6 new Pydantic models (SupportLevel, SupportTransition, GradualReleaseOutput, ComponentSkill, ComplexTask, DecompositionOutput)
- `tests/evals/rubrics/scaffolding_gradual_release.md` - Gradual release judge prompt
- `tests/evals/rubrics/scaffolding_decomposition.md` - Decomposition judge prompt
- `scripts/run_scaffolding_evals.py` - Extended runner (4 judges, 4 compute, 4 format functions)
- `app/langfuse/criteria.py` - 2 new registry entries

### 017 - Feedback Collector
**Status:** Implemented
**Spec:** [017-feedback-collector/spec.md](./017-feedback-collector/spec.md)
**Description:** ReAct agent that collects optional user feedback after lesson generation. Parses feedback into structured data (category, rating, text) and persists to DynamoDB.

**Features:**
- ReAct agent with `create_agent` from `langchain.agents`
- `submit_feedback(category, rating, text)` and `skip_feedback()` tools
- FeedbackService for DynamoDB persistence (single-table design)
- Graph routing: generator → feedback_collector → END
- Entry router handles mid-feedback resumption
- ChatService integration for auth-agnostic persistence

**Related Files:**
- `app/graph/agents/feedback_collector.py` - Feedback collector agent and tools
- `app/services/feedback_service.py` - DynamoDB feedback read/write service
- `app/graph/state.py` - `FeedbackData` TypedDict, `feedback_submitted` field
- `app/graph/graph.py` - `feedback_collector_node`, routing updates
- `app/services/chat_service.py` - Feedback persistence after graph invocation
- `app/models.py` - `Feedback` Pydantic model
- `app/db_schema.py` - `FEEDBACK_KEY_PATTERNS` documentation
- `scripts/init_db.py` - `validate_table_support()` GSI1 check
- `tests/unit/test_feedback_service.py` - Unit tests (4/4)
- `tests/evals/test_feedback_collector.py` - Node evals (5/5)
- `scripts/test_feedback_e2e.py` - E2E smoke test

### 018 - Verbatim & Structure LLM Judge Evals
**Status:** Implemented
**Spec:** [018-verbatim-structure-evals/spec.md](./018-verbatim-structure-evals/spec.md)
**Description:** Two new LLM judge evals for Form B format compliance. Checks whether generated lessons quote [Explanation] texts verbatim and include all required sections/markers. Also refactors the eval runner to a registry/dispatch pattern with selective `--eval` flag.

**Features:**
- Verbatim eval: checks if [Explanation] blocks quote Form B text word-for-word (5 sections)
- Structure eval: checks if all 8 required sections and 7 required markers are present and used correctly (15 checks)
- `--eval` CLI flag for selective eval execution (any combination of 6 evals)
- `EVAL_REGISTRY` dispatch pattern — adding new evals requires only a dict entry + 3 functions
- Dynamic report/summary adapts columns to whichever evals were selected
- Lazy form loading (Form B only loaded when verbatim/structure evals selected)

**Related Files:**
- `tests/evals/models.py` - 5 new Pydantic models (VerbatimSection, VerbatimOutput, SectionPresence, MarkerCheck, StructureOutput)
- `tests/evals/rubrics/verbatim_explanations.md` - Verbatim explanations judge prompt
- `tests/evals/rubrics/lesson_structure.md` - Lesson structure judge prompt
- `scripts/run_scaffolding_evals.py` - Refactored runner with EVAL_REGISTRY and --eval flag
- `app/langfuse/criteria.py` - 2 new registry entries

### 021 - Lesson Image Generation & PDF Export
**Status:** Implemented
**Spec:** [021-lesson-image-generation/spec.md](./021-lesson-image-generation/spec.md)
**Description:** LLM-powered image director agent that reads completed lesson plans, generates contextually relevant educational images via Gemini 2.5 Flash, and delivers them asynchronously. Includes PDF export for print-ready lesson plans.

**Features:**
- Image director agent (gpt-4o) reads lesson → outputs 3 image generation prompts
- Gemini 2.5 Flash image generation with parallel execution (ThreadPoolExecutor)
- S3 storage with pre-known URLs (images appear without coordination)
- Image data included in chat response for frontend rendering
- PDF export via weasyprint with print-optimized layout
- MarkdownRenderer updated with image styling + lazy loading
- Export PDF button in chatbot UI
- 22 unit tests (16 image generation + 6 PDF export)

**Related Files:**
- `app/services/image_service.py` - Gemini image generation + S3 upload
- `app/graph/nodes/image_assembly.py` - Pre-known URL computation
- `app/graph/nodes/image_director.py` - LLM prompt planning + generation orchestration
- `app/schemas/image.py` - ImageRequest, ImagePlan Pydantic models
- `app/schemas/chat.py` - ImageReadyEvent schema
- `app/routers/export.py` - PDF export endpoint
- `app/graph/state.py` - `image_requests`, `image_urls` state fields
- `app/graph/graph.py` - Image assembly + director nodes, routing updates
- `app/services/chat_service.py` - Image data in response
- `app/main.py` - Export router registration
- `frontend/src/components/MarkdownRenderer.jsx` - Image rendering support
- `frontend/src/components/Chatbot2.jsx` - Export PDF button + image state tracking
- `frontend/src/api/index.js` - `exportPdf()` API method
- `tests/unit/test_image_generation.py` - 16 unit tests
- `tests/unit/test_pdf_export.py` - 6 unit tests
- `Dockerfile` - WeasyPrint system dependencies
- `requirements.txt` - weasyprint, markdown packages

---

## How to Use This Structure

### When Adding a New Feature:
1. Create a new folder with the next number: `00X-feature-name/`
2. Write the spec in `spec.md`
3. Create empty subdirectories: `reviews/`, `incidents/`, `decisions/`
4. Update this README with the new feature

### When Documenting Issues:
Add to the feature's `incidents/` folder with sequential numbering:
- `001-issue-name.md`
- `002-another-issue.md`

### When Writing Reviews:
Add to the feature's `reviews/` folder with sequential numbering:
- `001-implementation.md` (post-implementation)
- `002-security-audit.md` (later reviews)

### When Making Architectural Decisions:
Add to the feature's `decisions/` folder with sequential numbering:
- `001-decision-name.md`
- `002-another-decision.md`

---

## Rebuilding the Application

To rebuild this application (even in a different language):
1. Read specs in numerical order (001, 002, 003...)
2. Check reviews for implementation notes and lessons learned
3. Review incidents to avoid known pitfalls
4. Consult decisions to understand the reasoning behind architectural choices
