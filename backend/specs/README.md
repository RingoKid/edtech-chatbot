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
**Status:** Implemented (v0.1)
**Spec:** [007-n8n-lesson-generator/spec.md](./007-n8n-lesson-generator/spec.md)
**Description:** n8n workflow for generating handwriting & spelling lesson plans. Used for prompt engineering experiments before Langfuse integration.

**Related Files:**
- `n8n/workflows/` - Exported workflow JSON files
- `n8n/experiments/changelog.md` - Experiment tracking
- `n8n/outputs/` - Sample lesson outputs

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
