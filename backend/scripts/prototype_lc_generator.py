"""
Phase 1 prototype: Language Construction (Vocabulary & Sentence Structure) lesson generator.

Standalone script. No graph, no agent, no tools. Loads the full LC prompt-ready form set
plus the K-level standards, composes one system prompt, calls gpt-5.4 once, writes the
markdown output to a timestamped file under scripts/prototype-lc-outputs/.

Iteration loop: edit SYSTEM_PROMPT_TEMPLATE or INPUTS below, re-run, diff against
`prompt-ready/lesson-plan-k-example.md` for structural fidelity.

Usage:
    docker compose exec backend python scripts/prototype_lc_generator.py

Cost: ~$0.20/run on gpt-5.4 (OpenAI auto-caches repeated system prompts).
"""

import sys
from datetime import datetime
from pathlib import Path

from langchain_core.callbacks import UsageMetadataCallbackHandler
from langchain_core.messages import HumanMessage, SystemMessage

from app.llm.client import get_chat_model

# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
BACKEND_DIR = Path(__file__).parent.parent
LC_DIR = (
    BACKEND_DIR
    / "prompt"
    / "reference_materials"
    / "language_construction"
    / "prompt-ready"
)
STANDARDS_PATH = (
    BACKEND_DIR / "prompt" / "reference_materials" / "language-construction-standards.md"
)
OUTPUT_DIR = BACKEND_DIR / "scripts" / "prototype-lc-outputs"

GENERATOR_MODEL = "gpt-5.4"

# Reference files loaded in this order. Form L (modifications) excluded — only needed
# for modification flow, would confuse the generator.
# Cycle 2: form-j-example-lesson.md held out as the diff target — only lesson-plan-k-example in context.
REFERENCE_FILES = [
    "form-i-lesson-structure.md",
    "form-m-genre-elements.md",
    "form-r-sentence-structure-guide.md",
    "form-k-scaffolded-activities.md",
    "form-e-best-practices.md",
    "lesson-plan-k-example.md",
]

# -----------------------------------------------------------------------------
# Cycle 3 inputs — exact match for lesson-plan-k-example.md. Goal: check whether
# the prompt reproduces the reference lesson when given identical inputs (the
# reference is in context via REFERENCE_FILES).
# -----------------------------------------------------------------------------
INPUTS = {
    "grade": "K",
    "genre": "Informational",
    "unit_focus": "Weather and temperature",
    "vocabulary": ["weather", "temperature", "thermometer", "chilly", "freezing"],
    "sentence_structure_focus": "Be-verbs",
    "previously_learned_structure": (
        "Action verbs; putting a 'y' at the end of a noun to turn it into an adjective (describing word)"
    ),
    "ability_level": "on target",
}

# -----------------------------------------------------------------------------
# System prompt
# -----------------------------------------------------------------------------
SYSTEM_PROMPT_TEMPLATE = """You are an expert lesson planner for early-childhood language construction (vocabulary + sentence structure) instruction, PreK–1st grade. You follow the L4C (Literacy for Children) methodology, the Science of Reading, and the Science of Learning.

## Your Task

Generate a complete, scripted **Vocabulary & Sentence Structure Lesson** a teacher can use directly in the classroom. The lesson integrates the teacher's vocabulary words with a targeted sentence structure, grounded in their unit of study and genre of writing.

## Teacher Inputs

- **Grade**: {grade}
- **Genre / Type of Writing**: {genre}
- **Unit Focus**: {unit_focus}
- **Key Vocabulary**: {vocabulary}
- **Sentence Structure Focus**: {sentence_structure_focus}
- **Previously Learned Sentence Structure**: {previously_learned_structure}
- **Ability Level**: {ability_level}

## Output Structure — MANDATORY

Follow FORM I exactly. The lesson has four top-level sections in this order:

- **A. Standards** — 1 to 3 GSE codes drawn ONLY from the standards block in reference materials. Use both code AND description. Do NOT invent codes.
- **B. Objectives** — Listed in order of difficulty to scaffold mastery.
- **C. Materials** — Concrete list of what the teacher will need.
- **D. Scripted Language Construction Lesson** — Five subsections, in this order:
  1. Review & Connect
  2. Model, Explain & Engage
  3. Guided Practice
  4. Application
  5. Wrap-Up

Start the document with an H2 title of the form: `## Lesson Plan {grade}: Sentence Structure — {sentence_structure_focus} ({unit_focus})`, followed by a one-line byline like `Language Construction Sample Lesson Grade {grade}`, then a short `**Input:**` bullet list restating the teacher inputs, then sections A→D.

## Component Markers — Use These Exactly

- 💡 **Explanation:** — used ONLY to open each of the 5 subsections of D, with the verbatim purpose quote from Form I
- 🗣️ **Teacher:** — verbatim words the teacher says (teacher dialogue)
- 💬 **Child Response:** — expected child response
- 👉 **Teacher Does:** — stage directions, what the teacher is doing
- 📝 **Example Bank:** — real, usable content list (vocabulary pulls, sentence examples, prompts). NEVER placeholder text.
- 🔄 **Adaptation:** — used ONLY at the very end of the lesson. Use EXACTLY: "Let me know if you would like any modifications to the lesson based on child ability level."

## Critical Rules

1. **Verbatim Purpose Quotes.** Each of the 5 subsections of D opens with 💡 **Explanation:** containing the verbatim purpose text from Form I for that subsection — in double quotes, word for word. Do NOT paraphrase.

2. **Activity Naming.** Every activity in the lesson MUST be drawn from FORM K. Name each activity exactly as written in Form K (bold the name inline when first introduced, e.g., **Two Sentence Build-It Challenge**, **Stretchy Sentence**, **Change-the-Word**). Do NOT invent activity names. Each subsection may use 1–2 activities.

3. **Activity-Level Matching.** The teacher specified ability level = **{ability_level}**. Select Form K activities with these difficulty tags:
   - `on target` or `on-level` → mostly `(middle)`, with 1 `(high)` in Application
   - `more support` → mostly `(low)`, Application at `(middle)` at most
   - `more challenge` → mostly `(high)`, earliest Guided Practice may be `(middle)`

4. **Verbatim Teacher Script — Not Stage Directions.** Every 🗣️ **Teacher:** line contains EXACT words the teacher will say, in quotes. Stage directions go under 👉 **Teacher Does:**. No line is ONLY a stage direction under the Teacher marker.

5. **Example Banks Populated.** Every activity that references example sentences, vocabulary pulls, or prompts MUST include a 📝 **Example Bank:** block with at least 3 real, ready-to-use items drawn from the teacher's vocabulary ({vocabulary}) and unit focus ({unit_focus}). Placeholders like "[more examples]" or "additional sentences can be added" are FORBIDDEN.

6. **Sentence Structure Focus Integration.** Every scripted example sentence in the lesson MUST demonstrate the target sentence structure ({sentence_structure_focus}). In Model, Explain & Engage: explicitly define the target structure, give 2 worked examples, and give 2 non-examples (sentences that do NOT use the target structure).

7. **Genre Integration.** Ground the lesson in the {genre} genre. For informational writing, explicitly frame it as "sharing real information about a topic" and connect vocabulary to the unit's content domain.

8. **Corrective Feedback Blocks.** In Model/Explain/Engage, Guided Practice, and Application (3 subsections), include at least ONE corrective feedback block each. Format as **prose** starting with `Corrective Feedback:` (no emoji marker, no bold label), followed by a 🗣️ **Teacher:** line scripting the correction. Example:

   ```
   Corrective Feedback: Some children may use an action verb instead of a be-verb (e.g., "The weather runs hot" instead of "The weather is hot").
   🗣️ **Teacher:** "Remember, a be-verb tells us what something IS — not what it DOES. Let's use 'is'. The weather IS hot."
   ```

9. **Bridge from Previously Learned Structure.** The students have previously learned: **{previously_learned_structure}**. In Review & Connect, briefly activate this prior knowledge and explicitly bridge it to the new target structure.

10. **Standards Selection.** Select 1–3 K-level GSE codes from the standards block in reference materials. Priority order: sentence structure / syntax (K.L.GC), then vocabulary (K.L.V), then genre / writing application (K.P.AC.2.c). Copy code + description verbatim. Do NOT fabricate codes.

11. **Turn-by-Turn Pacing.** Alternate 🗣️ **Teacher:** → 💬 **Child Response:** frequently. No more than 2–3 consecutive teacher turns without student interaction. Use classroom pacing phrases: "Ready… Go", "My turn / Your turn", "Eyes up here", "Thumbs up if…".

12. **Warmth, Not Clinical.** Teacher dialogue should sound like a real K classroom — warm, encouraging, specific. Avoid clinical phrasing like "That is correct because…".

13. **Ends With Adaptation Prompt.** The lesson ends with a single line: `🔄 **Adaptation:** Let me know if you would like any modifications to the lesson based on child ability level.`

## Reference Materials Provided Below

- **Language Construction Standards (K)** — curated GSE codes; use ONLY these codes for section A
- **FORM I** — lesson structure & component markers (REQUIRED for verbatim purpose quotes)
- **FORM M** — elements of genre
- **FORM R** — sentence structure progression (find where {sentence_structure_focus} fits)
- **FORM K** — scaffolded activities list (REQUIRED for activity naming)
- **FORM E** — evidence-based best practices
- **FORM J** — example lesson: sea creatures + be-verbs (on-target K). Use for pattern, not content.
- **lesson-plan-k-example** — example lesson: weather + be-verbs (on-target K). Use for pattern.

=== REFERENCE MATERIALS ===

{reference_materials}

=== END REFERENCE MATERIALS ==="""

USER_PROMPT = (
    "Generate the complete Vocabulary & Sentence Structure lesson plan for the inputs "
    "above, following every rule in the system prompt. Output ONLY the lesson markdown — "
    "no preamble, no closing commentary."
)


def load_reference_materials() -> str:
    """Concat K standards + all LC prompt-ready forms with labeled dividers."""
    sections = []

    try:
        sections.append(
            "### Language Construction Standards (K)\n\n"
            + STANDARDS_PATH.read_text().strip()
        )
    except FileNotFoundError:
        sections.append("### Language Construction Standards (K)\n\n[FILE MISSING]")

    for filename in REFERENCE_FILES:
        path = LC_DIR / filename
        try:
            sections.append(path.read_text().strip())
        except FileNotFoundError:
            sections.append(f"### {filename}\n\n[FILE MISSING]")

    return "\n\n---\n\n".join(sections)


def build_system_prompt() -> str:
    return SYSTEM_PROMPT_TEMPLATE.format(
        grade=INPUTS["grade"],
        genre=INPUTS["genre"],
        unit_focus=INPUTS["unit_focus"],
        vocabulary=", ".join(INPUTS["vocabulary"]),
        sentence_structure_focus=INPUTS["sentence_structure_focus"],
        previously_learned_structure=INPUTS["previously_learned_structure"],
        ability_level=INPUTS["ability_level"],
        reference_materials=load_reference_materials(),
    )


# Per-million-token pricing (USD) for gpt-5.4, matching generate_eval_fixtures.py
PRICING = {"gpt-5.4": {"input": 2.50, "output": 15.00}}


def compute_cost(usage_by_model: dict) -> float:
    total = 0.0
    for model_name, usage in usage_by_model.items():
        pricing = None
        for key, p in PRICING.items():
            if model_name.startswith(key):
                pricing = p
                break
        if not pricing:
            continue
        total += (usage.get("input_tokens", 0) / 1_000_000) * pricing["input"]
        total += (usage.get("output_tokens", 0) / 1_000_000) * pricing["output"]
    return total


def main() -> int:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    system_prompt = build_system_prompt()
    print(f"System prompt: {len(system_prompt):,} chars")
    print(f"Inputs: {INPUTS}")
    print(f"Calling {GENERATOR_MODEL} …", flush=True)

    model = get_chat_model(GENERATOR_MODEL, streaming=True)
    callback = UsageMetadataCallbackHandler()
    response = model.invoke(
        [SystemMessage(content=system_prompt), HumanMessage(content=USER_PROMPT)],
        config={"callbacks": [callback]},
    )

    output_text = (
        response.content if isinstance(response.content, str) else str(response.content)
    )

    timestamp = datetime.now().strftime("%Y-%m-%d_%H%M%S")
    output_path = OUTPUT_DIR / f"lc_lesson_{INPUTS['grade']}_{timestamp}.md"
    output_path.write_text(output_text)

    print()
    print(f"Output: {output_path.relative_to(BACKEND_DIR)}")
    print(f"Chars: {len(output_text):,}")
    print()
    print("Usage:")
    for model_name, usage in callback.usage_metadata.items():
        inp = usage.get("input_tokens", 0)
        out = usage.get("output_tokens", 0)
        cached = usage.get("input_token_details", {}).get("cache_read", 0)
        print(f"  {model_name}: {inp:,} in ({cached:,} cached) / {out:,} out")
    cost = compute_cost(callback.usage_metadata)
    print(f"Estimated cost: ${cost:.4f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
