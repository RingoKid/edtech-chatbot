-----

### FEATURE SPEC: 000 - Project Common

*(Included for context - see original file for full content)*

  * **Core Architectural Principles:** LangGraph, Unified State, Pydantic Tool Routing, `interrupt_after` Pausing.
  * **Execution Environment:** All commands via `docker compose exec backend ...`
  * **Workflow:** Implement -> Rebuild (`docker compose down && docker compose up -d --build`) -> Test (`docker compose exec backend pytest ...`) -> Fix -> Sync Spec.

-----

### FEATURE SPEC: 006 - Dynamic Prompt Builder and Lesson Generation

**Reference:** This builds upon `FEATURE SPEC: 000 - Project Common`, `FEATURE SPEC: 001 - Greeting & Main Router`, `FEATURE SPEC: 002 - Main Router Clarification Loop`, `FEATURE SPEC: 003 - Dynamic Parameter Collection`, `FEATURE SPEC: 004 - Expand Handwriting Parameters`, and `FEATURE SPEC: 005 - Expand Vocabulary and Idea Generation Parameters`. Assumes Docker execution environment as defined in `000`.

**Objective:** Replace the stub lesson generation node with a complete implementation that dynamically builds task-specific prompts from JSON form templates and generates structured lesson plans. The system must intelligently select and assemble relevant forms based on task type and query type, then use an LLM to generate complete, formatted lesson plans.

**Key Design Principles:**
1. **Dynamic Form Selection:** Only load forms relevant to the specific query type
2. **Structured Output:** Use Pydantic schemas for validated lesson structure
3. **Testability:** All components can be unit tested independently
4. **Traceability:** Track which forms were used in prompt assembly
5. **Efficiency:** Single node handles both prompt building and lesson generation

---

## Architecture Overview

```
Parameter Collection (Existing)
    ↓
Generate Lesson Node (NEW - replaces stub)
    ↓
END
```

**New State Fields:**
- `prompt_metadata`: Metadata about forms used and sections included
- `generated_lesson`: The structured lesson output

**Note:** The prompt building happens inside the `generate_lesson_node` as it's just string assembly with no LLM calls. No need for a separate node.

---

## Form Relationship Map

**Handwriting Forms:**
- **Form-B**: Master structure template (5 sections, formatting conventions)
- **Form-C**: Detailed scripted template with placeholders
- **Form-D**: Activity bank (4 adaptation categories by section)
- **Form-F**: Letter formation sequence verbal cues (all letters)
- **Form-G**: Phoneme gestures (all sounds)
- **Form-H**: Modification examples by ability level
- **Form-A**: Scaffolded verbs for objectives
- **Example_Handwriting&Spelling.json**: Complete reference lesson

**Vocabulary Forms:**
- **Form-K**: Activity bank for vocabulary/sentence structure
- **Form-L**: Modification examples for sentence structure
- **Form-A**: Scaffolded verbs for objectives

**Idea Generation Forms:**
- **FORM-P**: Activity bank for idea generation/organization
- **Form-A**: Scaffolded verbs for objectives

---

## Implementation Details

### 1. File: `app/graph/state.py`

**Action:** Add new fields to `GraphState` for lesson generation.

**Content:**

```python
# [Modify Schema - Add new fields at end]
class GraphState(TypedDict):
    """
    The unified state object for the entire graph.
    """
    messages: Annotated[List[BaseMessage], add_messages]
    task_name: Optional[str]

    # Parameter collection fields (existing)
    parameter_schema_name: Optional[str]
    required_parameters: List[str]
    collected_parameters: Dict[str, Any]
    current_question: Optional[str]
    collection_error_message: Optional[str]
    
    # NEW: Lesson generation fields
    prompt_metadata: Optional[Dict[str, Any]]
    generated_lesson: Optional[Dict[str, Any]]
```

**Rationale:** These new fields track the lesson generation process, allowing for debugging and traceability. Note: We don't store `lesson_prompt` in state since it's only used internally within the node.

---

### 2. File: `app/utils/form_loader.py` (NEW)

**Action:** Create a utility module for loading and caching JSON forms.

**Key Methods:**
- `load_form(form_name)`: Load a single form with caching
- `load_multiple_forms(form_names)`: Load multiple forms at once
- `get_forms_for_task(task_type, query_type)`: Get all relevant forms for a task
- `_get_handwriting_forms(query_type)`: Handwriting-specific form selection
- `_get_vocabulary_forms(query_type)`: Vocabulary-specific form selection
- `_get_idea_generation_forms(query_type)`: Idea generation-specific form selection

**Form Selection Logic:**

**Handwriting:**
- Base forms (always): Form-A, Form-B, Form-C, Form-F, Form-G, Form-H
- letter formation: + Form-D, Example
- fine motor: + Form-D
- spelling: + Form-D
- assessment: + Example
- general: + Form-D, Example

**Vocabulary:**
- All query types: Form-A, Form-K, Form-L

**Idea Generation:**
- All query types: Form-A, FORM-P

**Implementation:** See full code in appendix (too long for inline).

**Rationale:** Centralized form loading with caching improves performance. The singleton pattern ensures forms are loaded once per application lifecycle.

#### Forms Directory and Configuration

- Default forms directory: `backend/data/Forms_Json`
- Override via environment variable `FORMS_DIR` (absolute or project-relative path)
- Recommendation: avoid special characters like `&` in filenames (prefer underscores). Example: use `Example_Handwriting_Spelling.json` instead of `Example_Handwriting&Spelling.json`.

Example resolution strategy (conceptual):

```python
from pathlib import Path
import os

PROJECT_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_FORMS_DIR = PROJECT_ROOT / "backend" / "data" / "Forms_Json"
FORMS_DIR = Path(os.getenv("FORMS_DIR", str(DEFAULT_FORMS_DIR))).resolve()
```

---

### 3. File: `app/services/prompt_builder.py` (NEW)

**Action:** Create the prompt builder service that assembles prompts from forms.

**Key Methods:**
- `build_prompt()`: Main entry point, delegates to task-specific builders
- `_build_handwriting_prompt()`: Assembles handwriting-specific prompt
- `_build_vocabulary_prompt()`: Assembles vocabulary-specific prompt
- `_build_idea_generation_prompt()`: Assembles idea generation-specific prompt
- `_get_handwriting_sections()`: Determines which sections to include based on query type
- `_get_letter_data(target_letters, form_f, form_g)`: Extracts letter-specific data
- `get_metadata()`: Returns metadata about prompt assembly

**Prompt Structure (Handwriting Example):**
1. Role definition
2. Lesson parameters (grade, focus, target letters)
3. Lesson structure (Form B)
4. Formatting requirements (Form B)
5. Scaffolded verbs (Form A)
6. Letter-specific information (Form F, Form G) - if applicable
7. Scripted lesson template (Form C) - filtered by sections
8. Activity options (Form D) - filtered by sections
9. Example lesson (Example_Handwriting&Spelling) - for reference
10. Generation instructions

**Implementation:** See full code in appendix.

**Rationale:** The `PromptBuilder` encapsulates all logic for assembling prompts. It dynamically selects forms and sections based on task/query type.

#### Prompt Compaction and Metadata

- Include only sections relevant to the current task/query type
- Cap included form fragments to a safe prompt budget (approx 8–12k chars total)
- For activity banks, include top-K items per section (e.g., K=3–5)
- Track the following metadata for traceability:
  - `forms_used`: list of form names included
  - `sections_included`: list of section identifiers included
  - `letters_included`: for handwriting, which letters were targeted
  - `token_estimate`: rough character/token count of the final prompt
  - `truncations`: which sources/sections were truncated and by how much

---

### 3.5. Model Routing (Context)

Provide a centralized model selection mechanism so nodes can request the best model for a task without hard-coding providers.

Contract
- `Context.get_model(task_name: str, query_type: Optional[str] = None, demand: str = "balanced") -> Model`
- Internally use a `ModelRouter` that maps `(task_name, query_type, demand)` to a provider+model configuration

Usage in node
- `model = context.get_model(task_name, collected_params.get("query_type"))`
- Prefer `model.with_structured_output(schema, strict=False)` when available
- Fallback: JSON-mode generation + robust parsing; on failure surface a helpful error to the user

Testing
- Allow injecting a `FakeModel` via `Context` to keep unit tests offline and deterministic

---

### 4. File: `app/schemas/lesson_output.py` (NEW)

**Action:** Create Pydantic schemas for structured lesson output.

**Content:**

```python
from pydantic import BaseModel, Field
from typing import Optional

class HandwritingLesson(BaseModel):
    """Structured output for handwriting lessons."""
    lesson_title: str
    standards: str
    objectives: str
    materials: str
    review_connect: Optional[str] = None
    model_explain_engage: Optional[str] = None
    guided_practice: Optional[str] = None
    application: Optional[str] = None
    wrap_up: Optional[str] = None
    target_grade: str
    query_type: str
    target_letters: Optional[str] = None

class VocabularyLesson(BaseModel):
    """Structured output for vocabulary lessons."""
    lesson_title: str
    standards: str
    objectives: str
    materials: str
    review_connect: str
    model_explain_engage: str
    guided_practice: str
    application: str
    target_grade: str
    query_type: str
    target_vocabulary: Optional[str] = None
    target_genre: Optional[str] = None

class IdeaGenerationLesson(BaseModel):
    """Structured output for idea generation lessons."""
    lesson_title: str
    standards: str
    objectives: str
    materials: str
    review_connect: str
    model_explain_engage: str
    guided_practice: str
    application: str
    target_grade: str
    query_type: str
    target_genre: str
    target_topic: str

LESSON_SCHEMA_REGISTRY = {
    "Handwriting": HandwritingLesson,
    "Vocabulary": VocabularyLesson,
    "Idea Generation": IdeaGenerationLesson
}
```

**Rationale:** Structured output schemas ensure the LLM generates properly formatted lessons with automatic validation.

#### Versions and Typing Notes

- Python version: ≥ 3.9
- Pydantic: v2 (uses `model_dump`)
- Prefer Enums/Literals for task and query types to reduce typos and improve validation; keep lesson body sections as `str` with guidance in prompts to render bullet-like formatting

---

### 5. File: `app/graph/nodes.py`

**Action:** Replace `stub_generate_lesson_node` with complete implementation.

**New Imports:**
```python
from app.services.prompt_builder import PromptBuilder
from app.schemas.lesson_output import LESSON_SCHEMA_REGISTRY
import json
```

**Replace: `stub_generate_lesson_node` -> `generate_lesson_node`**

```python
def generate_lesson_node(state: GraphState) -> dict:
    """
    Generates a structured lesson plan.
    Builds the prompt internally, then uses LLM to generate the lesson.
    """
    task_name = state.get("task_name")
    collected_params = state.get("collected_parameters", {})
    
    print(f"DEBUG generate_lesson_node: task={task_name}, params={collected_params}")
    
    try:
        # Step 1: Build the prompt (no LLM call, just string assembly)
        builder = PromptBuilder(task_name, collected_params)
        lesson_prompt = builder.build_prompt()
        metadata = builder.get_metadata()
        
        print(f"DEBUG: Prompt built. Forms used: {metadata['forms_used']}")
        
        # Step 2: Generate the lesson using LLM
        context = Context()
        llm = context.model
        
        # Get the appropriate lesson schema
        lesson_schema = LESSON_SCHEMA_REGISTRY.get(task_name)
        if not lesson_schema:
            raise ValueError(f"No lesson schema found for task: {task_name}")
        
        # Use structured output for validated lesson generation
        structured_llm = llm.with_structured_output(lesson_schema, strict=False)
        
        # Generate the lesson
        lesson = structured_llm.invoke(lesson_prompt)
        
        # Convert to dict for storage
        lesson_dict = lesson.model_dump()
        
        print(f"DEBUG: Lesson generated successfully")
        
        # Format lesson for display
        display_content = format_lesson_for_display(lesson_dict, task_name)
        
        return {
            "generated_lesson": lesson_dict,
            "prompt_metadata": metadata,
            "messages": [AIMessage(content=display_content)]
        }
    
    except Exception as e:
        print(f"ERROR in generate_lesson_node: {e}")
        error_message = AIMessage(
            content=f"Error generating lesson: {str(e)}. Please try again."
        )
        return {"messages": [error_message]}


def format_lesson_for_display(lesson: dict, task_name: str) -> str:
    """
    Format the structured lesson for user-friendly display.
    """
    lines = [
        f"# {lesson.get('lesson_title', 'Lesson Plan')}",
        "",
        f"**Grade Level:** {lesson.get('target_grade')}",
        f"**Focus Area:** {lesson.get('query_type')}",
        ""
    ]
    
    # Add task-specific metadata
    if task_name == "Handwriting" and lesson.get('target_letters'):
        lines.append(f"**Target Letters:** {lesson['target_letters']}")
        lines.append("")
    elif task_name == "Vocabulary":
        if lesson.get('target_vocabulary'):
            lines.append(f"**Target Vocabulary:** {lesson['target_vocabulary']}")
        if lesson.get('target_genre'):
            lines.append(f"**Genre:** {lesson['target_genre']}")
        lines.append("")
    elif task_name == "Idea Generation":
        lines.append(f"**Genre:** {lesson.get('target_genre')}")
        lines.append(f"**Topic:** {lesson.get('target_topic')}")
        lines.append("")
    
    # Add main sections
    lines.extend([
        "## Standards",
        lesson.get('standards', 'N/A'),
        "",
        "## Objectives",
        lesson.get('objectives', 'N/A'),
        "",
        "## Materials",
        lesson.get('materials', 'N/A'),
        "",
        "## Lesson Plan",
        ""
    ])
    
    # Add lesson sections
    section_map = {
        'review_connect': 'Review & Connect',
        'model_explain_engage': 'Model, Explain & Engage',
        'guided_practice': 'Guided Practice',
        'application': 'Application',
        'wrap_up': 'Wrap-Up'
    }
    
    for key, title in section_map.items():
        if lesson.get(key):
            lines.extend([
                f"### {title}",
                lesson[key],
                ""
            ])
    
    lines.append("---")
    lines.append("*Lesson plan generated successfully. You can now use this with your students!*")
    
    return "\n".join(lines)
```

**Rationale:** Separating prompt building from generation allows for better testing and debugging. The structured output ensures consistent lesson format.

#### Imports and Behavior Notes

- Imports (adjust to your project equivalents):
  - `from app.core.context import Context`
  - `from langchain_core.messages import AIMessage`
  - `from langgraph.graph import END`
- Validate presence of `task_name` and required parameters before building the prompt; if missing, return a friendly message and route back to parameter collection
- Replace `print` with structured logging (or Python `logging`); keep internal logs separate from user-visible messages
- Ensure returned messages are appended per the `add_messages` contract, not overwriting conversation history
- Obtain model via `Context.get_model(task_name, collected_params.get("query_type"), demand="balanced")`
- Use a safe structured-output invocation with fallback (see below)

---

### 6. File: `app/graph/graph.py`

**Action:** Update graph to use the new `generate_lesson_node`.

**Changes:**

```python
# [Update imports]
from app.graph.nodes import (
    greeting_node,
    main_router,
    clarification_node,
    setup_handwriting,
    setup_vocabulary,
    setup_idea_generation,
    collect_parameters_node,
    wait_for_user_input,
    generate_lesson_node,  # RENAMED from stub_generate_lesson_node
    route_from_main_router,
    route_parameter_collection
)

# [In create_graph function, update node]
async def create_graph():
    # ... existing setup ...
    
    # Add nodes
    graph.add_node("greeting_node", greeting_node)
    graph.add_node("main_router", main_router)
    graph.add_node("clarification", clarification_node)
    graph.add_node("setup_handwriting", setup_handwriting)
    graph.add_node("setup_vocabulary", setup_vocabulary)
    graph.add_node("setup_idea_generation", setup_idea_generation)
    graph.add_node("collect_parameters", collect_parameters_node)
    graph.add_node("wait_for_input", wait_for_user_input)
    graph.add_node("generate_lesson", generate_lesson_node)  # UPDATED
    
    # ... existing edges ...
    
    # Parameter collection edges (no changes needed)
    graph.add_conditional_edges(
        "collect_parameters",
        route_parameter_collection,
        {
            "wait_for_input": "wait_for_input",
            "generate_lesson": "generate_lesson"  # Routes directly to generate_lesson
        }
    )
    graph.add_edge("wait_for_input", "collect_parameters")
    graph.add_edge("generate_lesson", END)
    
    # ... rest of function ...
```

**Rationale:** Simpler flow with one less node. The `generate_lesson_node` handles both prompt building and lesson generation internally.

---

### Model Routing (Context)

Provide a central `Context` for model access with an internal `ModelRouter`:

- API: `Context.get_model(task_name: str, query_type: Optional[str] = None, demand: str = "balanced") -> Model`
- Routing: (task, query) → provider/model config; configurable via env or a small mapping
- Node usage: `model = context.get_model(task_name, collected_params.get("query_type"))`

Structured Output Fallback

- Primary: `model.with_structured_output(schema, strict=False)`
- Fallback: JSON-mode + robust parse; on failure, return a helpful user message and log the internal error
- Testing: allow injection of a `FakeModel` via Context to avoid network access

---

### 7. Unit Tests

**File:** `tests/test_form_loader.py` (NEW)

**Test Cases:**
- `test_load_single_form_success`: Test loading a single form
- `test_load_form_caching`: Verify forms are cached after first load
- `test_load_nonexistent_form`: Test error handling for missing forms
- `test_load_multiple_forms`: Test batch loading
- `test_get_handwriting_forms_letter_formation`: Verify correct forms for letter formation
- `test_get_handwriting_forms_fine_motor`: Verify correct forms for fine motor
- `test_get_vocabulary_forms`: Verify vocabulary forms
- `test_get_idea_generation_forms`: Verify idea generation forms
- `test_clear_cache`: Test cache clearing functionality

**File:** `tests/test_prompt_builder.py` (NEW)

**Test Cases:**
- `test_build_handwriting_prompt_letter_formation`: Test handwriting prompt with target letters
- `test_build_handwriting_prompt_no_letters`: Test handwriting prompt without target letters
- `test_build_vocabulary_prompt`: Test vocabulary prompt assembly
- `test_build_idea_generation_prompt`: Test idea generation prompt assembly
- `test_get_letter_data_single_letter`: Test letter data extraction for one letter
- `test_get_letter_data_multiple_letters`: Test letter data extraction for multiple letters
- `test_get_handwriting_sections_letter_formation`: Verify correct sections for letter formation
- `test_get_handwriting_sections_fine_motor`: Verify correct sections for fine motor
- `test_prompt_metadata`: Verify metadata is correctly populated

**File:** `tests/test_lesson_generation.py` (NEW)

**Test Cases:**
- `test_generate_lesson_node_handwriting`: Test full lesson generation for handwriting
- `test_generate_lesson_node_vocabulary`: Test full lesson generation for vocabulary
- `test_generate_lesson_node_idea_generation`: Test full lesson generation for idea generation
- `test_generate_lesson_node_error_handling`: Test error handling in generate_lesson_node
- `test_generate_lesson_node_missing_params`: Test error handling when params are missing
- `test_format_lesson_for_display`: Test lesson formatting function
- `test_generate_lesson_with_multiple_letters`: Test handwriting with multiple target letters
- `test_generate_lesson_metadata_tracking`: Verify metadata is correctly populated

**File:** `tests/test_lesson_generation_integration.py` (NEW)

**Integration Test Cases:**
- `test_full_handwriting_flow_letter_formation`: Complete flow from greeting to lesson generation
- `test_full_vocabulary_flow`: Complete vocabulary lesson flow
- `test_full_idea_generation_flow`: Complete idea generation lesson flow
- `test_handwriting_flow_with_multiple_letters`: Test with multiple target letters
- `test_lesson_contains_required_sections`: Verify all required sections are present
- `test_lesson_follows_formatting_requirements`: Verify formatting conventions are followed

**Run tests:**

```bash
# Run all new tests
docker compose exec backend pytest tests/test_form_loader.py tests/test_prompt_builder.py tests/test_lesson_generation.py tests/test_lesson_generation_integration.py -v

# Run specific test file
docker compose exec backend pytest tests/test_lesson_generation_integration.py -v

# Run with coverage
docker compose exec backend pytest tests/ --cov=app.services --cov=app.utils --cov=app.graph.nodes -v
```

*(Refer to `FEATURE SPEC: 000` for full Docker execution workflow)*

#### Test Fixtures and Mocks

- Set `FORMS_DIR` in tests to point to a temporary directory with small JSON fixtures
- Ensure `FormLoader.clear_cache()` is called between tests that mutate forms
- Provide a `FakeModel` and/or mock `Context.get_model` so tests do not hit the network
- Add tests that verify metadata presence (`forms_used`, `sections_included`, `token_estimate`, `truncations`) and compaction behavior
- Add a test to assert message appending preserves prior conversation content

---

### 8. LangSmith Evaluation Strategy

**Dataset:** "Feature 6: Dynamic Lesson Generation"

**Examples:** Create multi-turn examples covering the full flow from parameter collection to lesson generation for all three task types.

**Example 1 (Handwriting - Letter Formation):**
- User: "Hello" -> AI: Greeting
- User: "Handwriting" -> AI: Grade question
- User: "Kindergarten" -> AI: Query type question
- User: "letter formation" -> AI: Target letters question
- User: "z" -> AI: Complete lesson plan for letter z

**Example 2 (Handwriting - Fine Motor):**
- User: "Hello" -> AI: Greeting
- User: "Handwriting" -> AI: Grade question
- User: "Pre-K" -> AI: Query type question
- User: "fine motor" -> AI: Target letters question
- User: "None" -> AI: Fine motor focused lesson

**Example 3 (Vocabulary):**
- User: "Hello" -> AI: Greeting
- User: "Vocabulary" -> AI: Grade question
- User: "First Grade" -> AI: Query type question
- User: "sentence structure" -> AI: Target vocabulary question
- User: "action verbs" -> AI: Target genre question
- User: "informational" -> AI: Complete vocabulary lesson

**Example 4 (Idea Generation):**
- User: "Hello" -> AI: Greeting
- User: "Idea Generation" -> AI: Grade question
- User: "Kindergarten" -> AI: Query type question
- User: "brainstorming" -> AI: Target genre question
- User: "narrative" -> AI: Target topic question
- User: "My Family" -> AI: Complete idea generation lesson

**Evaluators:**

1. **"Prompt Assembly Correctness" (Custom Code/JSON)**
   - Check that `state.prompt_metadata.forms_used` contains the correct forms for the task/query type
   - Verify `state.prompt_metadata.sections_included` matches expected sections
   - Ensure metadata is populated after lesson generation

2. **"Lesson Structure Completeness" (Custom Code/JSON)**
   - Verify `state.generated_lesson` contains all required fields (title, standards, objectives, materials)
   - Check that appropriate lesson sections are present based on query type
   - For handwriting letter formation: verify all 5 sections are present
   - For handwriting fine motor: verify guided_practice section is present
   - For vocabulary/idea generation: verify all 4 main sections are present

3. **"Lesson Formatting Requirements" (Regex/String Match)**
   - For handwriting lessons, check that formatting markers are present (#, +, *, ##, {}, (), [])
   - Verify teacher scripts are marked with #
   - Verify gestures are marked with +
   - Verify adaptations are marked with *
   - Verify sequence verbal cues are marked with ##

4. **"Parameter Integration" (Custom Code/JSON)**
   - Verify target_grade in lesson matches collected parameter
   - Verify query_type in lesson matches collected parameter
   - For handwriting: verify target_letters matches (if provided)
   - For vocabulary: verify target_vocabulary and target_genre match
   - For idea generation: verify target_genre and target_topic match

5. **"Letter-Specific Data Inclusion" (Custom Code/String Match)**
   - For handwriting lessons with target letters, verify:
     - Sequence verbal cues for the target letter(s) are present
     - Phoneme gesture for the target sound is present
     - Letter formation instructions reference the specific letter

6. **"Activity Selection Appropriateness" (LLM-as-Judge)**
   - Use an LLM evaluator to assess if selected activities match the query type
   - For letter formation: should include Sound Hunt, Trace & Say, etc.
   - For fine motor: should include Magic Finger Write, Sky Writing, etc.
   - For spelling: should include Sound-Letter Hunt, Write the Sound, etc.

7. **"Grade-Level Appropriateness" (LLM-as-Judge)**
   - Use an LLM evaluator to assess if lesson complexity matches target grade
   - Pre-K lessons should be simpler with more scaffolding
   - First Grade lessons can be more complex

8. **"Lesson Coherence and Quality" (LLM-as-Judge)**
   - Use an LLM evaluator to assess overall lesson quality
   - Check for logical flow between sections
   - Verify teacher scripts are clear and actionable
   - Ensure materials list matches activities described

**Evaluation Metrics:**
- Success Rate: % of examples where all evaluators pass
- Prompt Assembly Accuracy: % of examples with correct forms selected
- Structural Completeness: % of lessons with all required sections
- Formatting Compliance: % of lessons following formatting requirements
- Parameter Fidelity: % of lessons correctly incorporating all parameters
- Overall Quality Score: Average LLM-as-Judge score (1-5 scale)

**Target Thresholds:**
- Success Rate: ≥ 90%
- Prompt Assembly Accuracy: ≥ 95%
- Structural Completeness: ≥ 95%
- Formatting Compliance: ≥ 85%
- Parameter Fidelity: ≥ 98%
- Overall Quality Score: ≥ 4.0/5.0

---

## Appendix: Full Code Implementations

### A. FormLoader Full Implementation

```python
"""
Utility for loading and caching JSON form templates.
"""
import json
from pathlib import Path
from typing import Dict, Any, Optional
import os


class FormLoader:
    """Singleton class for loading and caching JSON form templates."""
    _instance: Optional['FormLoader'] = None
    _forms_cache: Dict[str, Dict[str, Any]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(FormLoader, cls).__new__(cls)
        return cls._instance

    @property
    def forms_dir(self) -> Path:
        """Resolve forms directory from env or default to backend/data/Forms_Json."""
        project_root = Path(__file__).resolve().parents[3]
        default_dir = project_root / "backend" / "data" / "Forms_Json"
        env_dir = os.getenv("FORMS_DIR")
        return Path(env_dir).resolve() if env_dir else default_dir.resolve()

    def load_form(self, form_name: str) -> Dict[str, Any]:
        """Load a specific form by name with caching."""
        if form_name in self._forms_cache:
            return self._forms_cache[form_name]

        form_path = self.forms_dir / f"{form_name}.json"

        if not form_path.exists():
            raise FileNotFoundError(f"Form file not found: {form_path}")

        with open(form_path, 'r', encoding='utf-8') as f:
            form_data = json.load(f)

        self._forms_cache[form_name] = form_data
        return form_data

    def load_multiple_forms(self, form_names: list[str]) -> Dict[str, Dict[str, Any]]:
        """Load multiple forms at once."""
        return {name: self.load_form(name) for name in form_names}

    def get_forms_for_task(self, task_type: str, query_type: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """Get all relevant forms for a specific task and query type."""
        if task_type == "Handwriting":
            return self._get_handwriting_forms(query_type)
        elif task_type == "Vocabulary":
            return self._get_vocabulary_forms(query_type)
        elif task_type == "Idea Generation":
            return self._get_idea_generation_forms(query_type)
        else:
            raise ValueError(f"Unknown task type: {task_type}")

    def _get_handwriting_forms(self, query_type: Optional[str]) -> Dict[str, Dict[str, Any]]:
        """Get forms specific to handwriting lessons."""
        base_forms = ["Form-A", "Form-B", "Form-C", "Form-F", "Form-G", "Form-H"]

        if query_type == "letter formation":
            forms = base_forms + ["Form-D", "Example_Handwriting_Spelling"]
        elif query_type == "fine motor":
            forms = base_forms + ["Form-D"]
        elif query_type == "spelling":
            forms = base_forms + ["Form-D"]
        elif query_type == "assessment":
            forms = base_forms + ["Example_Handwriting_Spelling"]
        else:
            forms = base_forms + ["Form-D", "Example_Handwriting_Spelling"]

        return self.load_multiple_forms(forms)

    def _get_vocabulary_forms(self, query_type: Optional[str]) -> Dict[str, Dict[str, Any]]:
        """Get forms specific to vocabulary lessons."""
        return self.load_multiple_forms(["Form-A", "Form-K", "Form-L"])

    def _get_idea_generation_forms(self, query_type: Optional[str]) -> Dict[str, Dict[str, Any]]:
        """Get forms specific to idea generation lessons."""
        return self.load_multiple_forms(["Form-A", "FORM-P"])

    def clear_cache(self):
        """Clear the forms cache."""
        self._forms_cache.clear()


def get_form_loader() -> FormLoader:
    """Get the FormLoader singleton instance."""
    return FormLoader()

---

## Implementation Plan (Actionable)

1) `app/utils/form_loader.py`
   - Add `FORMS_DIR` env override and robust path resolution to default `backend/data/Forms_Json`
   - Keep in-memory cache; add `clear_cache()`; improve missing file errors

2) `app/core/context.py` (NEW)
   - Implement `ModelRouter` and `Context.get_model(task_name, query_type=None, demand="balanced")`
   - Support injecting a `FakeModel` for tests

3) `app/services/model_utils.py` (NEW)
   - `safe_structured_invoke(model, schema, prompt)`: try structured output → JSON-mode + parse → helpful error

4) `app/schemas/lesson_output.py`
   - Add enums/literals for task/query types; confirm Pydantic v2 usage

5) `app/services/prompt_builder.py`
   - Add metadata keys; apply compaction and section filtering rules

6) `app/graph/nodes.py`
   - Logging, param validation, message appending; use `Context.get_model` + safe structured invoke

7) `app/graph/state.py` and `app/graph/graph.py`
   - Ensure imports, new fields, and node wiring updates

8) `tests/`
   - Fixtures for forms dir and cache; mock `Context`/model; compaction tests; message appending test

9) Config/Docs
   - Docker env (`FORMS_DIR`), requirements pins, quick README for forms and model router

---

## Implementation Plan (Actionable)

1) `app/utils/form_loader.py`
   - Add `FORMS_DIR` env override and robust path resolution
   - Keep in-memory cache; add `clear_cache()`; improve error messaging
2) `app/core/context.py` (NEW)
   - Implement `ModelRouter` and `Context.get_model()`; support `FakeModel` injection
3) `app/services/model_utils.py` (NEW)
   - `safe_structured_invoke()`: structured → JSON-mode fallback → clear error
4) `app/schemas/lesson_output.py`
   - Add enums/literals for task/query types; keep Pydantic v2
5) `app/services/prompt_builder.py`
   - Add metadata keys; apply compaction and section filtering
6) `app/graph/nodes.py`
   - Logging, parameter guards, message appending; use `Context.get_model` + safe invoke
7) `app/graph/state.py` and `app/graph/graph.py`
   - Ensure imports, new fields, and node wiring
8) `tests/`
   - Fixtures for forms dir and cache; mock Context/model; compaction tests
9) Config/docs
   - Docker env (`FORMS_DIR`), requirements pins, quick README for forms and router
```

---

## Summary

This feature implements a complete, production-ready lesson generation system that:

✅ **Dynamically selects** relevant forms based on task and query type
✅ **Assembles comprehensive prompts** with all necessary instructions and templates
✅ **Generates structured lessons** with validated output schemas
✅ **Maintains traceability** through metadata tracking
✅ **Provides error handling** at each step
✅ **Supports all three task types** (Handwriting, Vocabulary, Idea Generation)
✅ **Includes comprehensive testing** (unit, integration, and LangSmith evals)

**Next Steps After Implementation:**
1. Run all unit tests to verify components work independently
2. Run integration tests to verify end-to-end flow
3. Set up LangSmith evaluations with example datasets
4. Review generated lessons for quality and formatting
5. Iterate on prompt templates based on evaluation results
6. Sync this spec with final working code

-----
