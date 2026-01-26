# Lesson Parameters Reference

This document defines the required parameters for each lesson type collected by the param agent.

---

## 1. Handwriting & Spelling

**Tool:** `submit_handwriting_params`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `grade` | `Literal["PreK", "K", "1st"]` | Yes | — | Grade level |
| `letter` | `str` | Yes | — | Target letter for the lesson |
| `student_level` | `Literal["struggling", "on-level", "advanced"]` | No | `"on-level"` | For modifications |

**Collection Questions:**
1. "What grade level is this lesson for?"
2. "What letter/sound are you focusing on?"

**Training Codes Input (simplified):**
- `Objective`: teacher will provide the objective focus of the lesson
- `Grade`: PreK, Kindergarten, First

> **Note:** The training codes use "objective" broadly, but spec 011 simplified this to `letter` since handwriting lessons typically focus on a single letter/sound. The system prompt asks: "what objectives you'd like to focus on for handwriting and spelling or tell me what letters and sounds you are currently focused on"

**Source:** `1AI_Trainng_Codes_Handwriting_and_Spelling.md`, System prompt line 54

---

## 2. Vocabulary & Sentence Structure

**Tool:** `submit_vocabulary_syntax_params`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `grade` | `Literal["PreK", "K", "1st"]` | Yes | — | Grade level |
| `writing_type` | `Literal["informational", "narrative", "personal_narrative", "opinion"]` | Yes | — | Genre/type of writing unit |
| `key_vocabulary` | `list[str]` | Yes | — | Vocabulary words teacher is working on |
| `objectives` | `str` | Yes | — | Teacher's objective focus (e.g., "be-verbs", "prepositional phrases") |
| `student_level` | `Literal["struggling", "on-level", "advanced"]` | No | `"on-level"` | For modifications |

**Collection Questions:**
1. "What grade level is this lesson for?"
2. "What type of writing is your unit focused on? (informational, opinion, narrative, or personal narrative)"
3. "What are some key vocabulary words related to your unit theme or topic?"
4. "What are the objectives for this lesson?"

**Source:** System prompt lines 121, 136-151

---

## 3. Idea Generation & Organization

**Tool:** `submit_idea_generation_params`

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `grade` | `Literal["PreK", "K", "1st"]` | Yes | — | Grade level |
| `genre` | `Literal["narrative", "informational", "opinion"]` | Yes | — | Type of genre |
| `genre_component` | `str` | Yes | — | Specific component to focus on (e.g., "relevant details", "topic sentence") |
| `writing_stage` | `Literal["brainstorm", "initial_draft", "revise", "edit"]` | Yes | — | Current stage in writing process |
| `objectives` | `str` | Yes | — | Teacher's objective focus |
| `student_level` | `Literal["struggling", "on-level", "advanced"]` | No | `"on-level"` | For modifications |

**Collection Questions (from training codes):**
1. "What is the grade level?"
2. "What is the genre focus (narrative, informational, opinion)?"
3. "What is the genre component of focus?" (e.g., topic sentence, relevant details)
4. "What is the writing stage (brainstorm, initial draft, revise, edit)?"
5. "What are the objectives for this lesson?"

**Optional Context (from initiating prompts):**
- Unit focus
- Books they've read in this unit
- Topic/purpose
- What they've already learned about the topic
- Vocabulary/sentence structure skills they've been working on

**Training Codes Input:**
- `Objective`: teacher will provide the objective focus of the lesson
- `Grade`: PreK, Kindergarten, First
- `Type of Genre`: narrative, informational, opinion
- `Genre Component Focus`: specific component (e.g., relevant details, topic sentence)
- `Writing Stage`: brainstorm, initial draft, revise, edit

**Source:** `3AI_Trainng_Codes_Idea_Generation_&_Organization.md` lines 26-50

---

## Common Patterns

### Shared Parameters

All lesson types share:
- `grade` — Always required, same options
- `student_level` — Always optional, same options, used for modifications

### Student Level Options

| Value | Description |
|-------|-------------|
| `struggling` | More support, reduced cognitive load |
| `on-level` | Standard lesson |
| `advanced` | More challenge, increased complexity |

---

## TypedDict Definitions

```python
from typing import Literal, TypedDict

class HandwritingParams(TypedDict):
    grade: Literal["PreK", "K", "1st"]
    letter: str
    student_level: Literal["struggling", "on-level", "advanced"]

class VocabularySyntaxParams(TypedDict):
    grade: Literal["PreK", "K", "1st"]
    writing_type: Literal["informational", "narrative", "personal_narrative", "opinion"]
    key_vocabulary: list[str]
    objectives: str
    student_level: Literal["struggling", "on-level", "advanced"]

class IdeaGenerationParams(TypedDict):
    grade: Literal["PreK", "K", "1st"]
    genre: Literal["narrative", "informational", "opinion"]
    genre_component: str
    writing_stage: Literal["brainstorm", "initial_draft", "revise", "edit"]
    objectives: str
    student_level: Literal["struggling", "on-level", "advanced"]
```

---

## References

- Original system prompt: `/Users/bdi-lab/Documents/Obsidian/10 Projects/EdTech/Current EdTech Instructions.md`
- Param agent spec: `backend/specs/011-param-agent/spec.md`
- Reference materials: `backend/prompt/reference_materials/`
