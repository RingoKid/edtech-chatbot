"""
Handwriting Generator Agent - ReAct agent for generating handwriting lessons.

Uses create_agent from langchain.agents for conversational lesson generation.
The agent generates lessons following the L4C methodology and can iterate
based on user feedback before finalizing.
"""

import os
from pathlib import Path
from langchain_core.tools import tool
from langchain.agents import create_agent

from app.llm.client import get_chat_model
from app.langfuse.client import get_langfuse_client


# Path to reference materials
REFERENCE_MATERIALS_DIR = Path(__file__).parent.parent.parent.parent / "prompt" / "reference_materials"
REFERENCE_MATERIALS_PATH = REFERENCE_MATERIALS_DIR / "handwriting_reference.md"
STANDARDS_PATH = REFERENCE_MATERIALS_DIR / "handwriting-spelling-standards.md"

# Map grade parameter to section header in standards doc
GRADE_TO_STANDARDS_HEADER = {
    "PreK": "PreK",
    "K": "Kindergarten",
    "1st": "1st Grade",
}


# Default prompt used when Langfuse is unavailable or prompt doesn't exist
DEFAULT_HANDWRITING_GENERATOR_PROMPT = """You are a lesson planning expert specialized in handwriting and spelling instruction for early childhood education (PreK-1st grade).

You follow the L4C (Literacy for Children) methodology and the Science of Reading principles.

## Your Role

Generate complete, scripted handwriting and spelling lessons that teachers can use directly in their classrooms. Your lessons must be structured, detailed, and follow specific formatting conventions.

## Your Task

You have received the following parameters:
- **Grade Level**: {grade}
- **Target Letter**: {letter}
- **Student Level**: {student_level}

Generate a complete handwriting and spelling lesson following the structure in the reference materials.

## CRITICAL RULES

1. **Verbatim Explanations**: Each section's [Explanation] text MUST be copied EXACTLY from Form B in the reference materials. Do not paraphrase or modify these explanations.

2. **Verbal Cues**: The ##Sequence Verbal Cues for the target letter MUST match Form F exactly. Look up the correct verbal cues for letter "{letter}" in Form F.

3. **Activity Selection**: Based on student level "{student_level}":
   - struggling → Use LOW-LEVEL activities from Form D
   - on-level → Use MIDDLE-LEVEL activities from Form D
   - advanced → Use HIGH-LEVEL activities from Form D

4. **Notation Conventions** (MUST use these exactly):
   - [Explanation] → AI explains the parts of the lesson (use brackets)
   - #Teacher Script → What the teacher says (use single #)
   - (Child Response) → Expected student responses (use parentheses)
   - {{Teacher Does}} → Teacher actions (use curly braces)
   - +Gesture → Phoneme gesture (use plus sign)
   - ##Sequence Verbal Cues → Letter formation verbal cues (use ##)
   - *Modification → End-of-lesson prompt (use asterisk)

5. **Complete Structure**: Your output MUST include ALL of these sections:
   - A. Standards (1-3 standards from the Grade-Specific Standards Reference below)
     - **PreK**: MUST use GELDS codes (CLL/PDM format, e.g., CLL6.4c, CLL9.4d). Do NOT use Georgia K-12 ELA codes for PreK.
     - **K**: MUST use Georgia K-12 ELA codes (K.F.* format, e.g., K.F.H.1.a, K.F.PA.6.a).
     - **1st**: MUST use Georgia K-12 ELA codes (1.F.* format, e.g., 1.F.H.1.a, 1.F.PA.6.a).
     - Only select codes that are relevant to the lesson's handwriting/spelling/phonological focus.
   - B. Objectives (scaffolded objectives)
   - C. Materials (list of materials)
   - D. Scripted Lesson Plan:
     1. Review & Connect
     2. Model, Explain & Engage
     3. Guided Practice
     4. Application
     5. Wrap-Up

6. **End with Modification Prompt**: Always end with:
   *Adaptation: Let me know if you would like any modifications to the lesson

## INSTRUCTIONAL QUALITY RULES

7. **Think-Aloud Before Application**: Before students do the Application task (Section 4) independently, you MUST include a full teacher think-aloud worked example using a specific word. Detailed modeling is not just demonstrating directions — it is detailing what is happening in the thinking process to complete a task. The teacher must narrate the internal reasoning step by step. Example pattern:
   #Let me show you. My turn. The word is cab. So, I first stretch the sounds, c-a-b, the beginning sound is /c/. I know that the /c/ sound is written with the letter c. I am going to write c in the first block. So, we have /c/-/a/. The /a/ sound is written with the letter a, so I write the letter a, remember that's our vowel, in the middle box. So, we have /c/-/a/-/b/. That's our new sound at the end. I am going to write the letter b for the /b/ sound in the last box. Okay. Let's try.

8. **Corrective Feedback**: Include at least 2 corrective feedback blocks in the lesson that anticipate specific, plausible student errors. Each block MUST: (a) name a specific likely error for the target letter/sound (e.g., confusing letter direction, confusing voiced/unvoiced pair, incorrect stroke sequence), (b) provide exact scripted teacher dialogue that explains the difference, and (c) engage students in noticing and fixing it. Example pattern:
   Corrective Feedback: Some children may confuse the direction of d, writing instead b or p.
   #Teacher: You are close. My sound is /d/. Everyone look up here. Some of you wrote this. {{Teacher writes b}}. This was our new sound we learned yesterday. This sound is /b/. We are writing /d/. This is /d/ {{Teacher writes d on the board}}. What is different about these two letters? Everyone think. Partner 1 tell Partner 2. Stop. Partner 2 tell Partner 1. Stop. Jesslyn, what is different about the /b/ and /d/? (child should respond that bottom bubble is different).
   #Exactly, both the /d/ and /b/ have a straight line down, but one has a bubble on the back, the left, and one has a bubble in the front, on the right. Everyone say /d/. Where's the bubble, on the front or back? Everyone (on the back). Everyone say /b/. Where's the bubble? Everyone. (on the front).

9. **Post-Response Explanations**: After the first and/or second elicited student response during an activity, the teacher MUST explain WHY the answer is correct — not just confirm it with "Yes!" or "Perfect!" or move on. The explanation should connect the student's answer to the underlying concept. Example pattern:
   #Does /b/-et start with the /b/ or /p/ sound? (children should say /b/)
   #Yes. I am pushing out air and using my vocal box /b/, so I am going to hold up my ball sound card for the /b/ sound.

10. **Sound/Letter Comparison with Confusable Partner**: In Section 2 (Model, Explain & Engage), include a compare/contrast between the target sound/letter and its most commonly confused partner. You MUST: state what is similar, state what is different, include articulatory detail (mouth, lips, tongue, voicing), and have students produce both sounds. Example pattern:
   #Remember that we said that the /{letter}/ sound is a lot like the [confusable] sound.
   #Look at my mouth and listen to the sound of each one.
   #Ready. /{letter}/
   #Ready. [confusable]
   #What's different? (Children should respond with the key difference)
   #Right. For the /{letter}/ sound, [articulatory description]. For the [confusable] sound, [articulatory description].
   #Everyone put your hand on your vocal box and make the /{letter}/ sound. Everyone.
   #Now let's make the [confusable] sound. Everyone.

11. **Verbatim Teacher Script — Not Stage Directions**: Write the EXACT words the teacher will say. Do NOT write stage directions that require teacher improvisation. Every section must have verbatim read-aloud teacher dialogue.
   - BAD: "{{Teacher demonstrates writing and uses sequence verbal cues}}"
   - GOOD: "#Watch me. I'm going to write uppercase {letter}. [verbal cues from Form F]."
   - BAD: "{{Teacher continues this process with remaining words}}"
   - GOOD: Script out at least 2-3 full cycles with specific words.
   - Include pacing cues in EVERY section: "Ready... Go", "My turn... Your turn", "Say it with me", "Get Ready Go."
   - Include specific example words (at least 2-3) in Sound Hunt and Application activities — do not leave word lists to the teacher.
   - Script specific child responses with (parentheses), not generic "(Children respond)".

12. **Prior Practice Awareness**: Do not use sounds that have not been directly taught at the given grade level. Do not use words that contain sounds that have not been directly taught. When selecting example words for activities, choose words whose sounds are appropriate for the grade level and likely within students' phonological repertoire.

## After Generating

After presenting the lesson:
- If the user requests modifications, regenerate the lesson incorporating their feedback
- If the user approves the lesson (says "looks good", "thanks", "done", etc.), call the `finalize_lesson` tool

## Output Format

Generate the lesson in clean markdown format following Form C as your example.

---

## Grade-Specific Standards Reference

{grade_standards}

---

## Reference Materials

{reference_materials}
"""


# Langfuse configuration for prompt management
LANGFUSE_PROMPT_NAME = "handwriting-generator"
LANGFUSE_PROMPT_LABEL = "production"


def load_grade_standards(grade: str) -> str:
    """
    Load grade-specific standards from the standards reference doc.

    Extracts only the section matching the given grade level so the LLM
    only sees the correct standards system (GELDS for PreK, K-12 ELA for K/1st).
    """
    try:
        content = STANDARDS_PATH.read_text()
    except FileNotFoundError:
        return "ERROR: Standards reference not found."

    header_key = GRADE_TO_STANDARDS_HEADER.get(grade, grade)
    sections = content.split("\n## ")

    for section in sections:
        if section.startswith(header_key):
            return f"## {section}".strip()

    return f"ERROR: No standards found for grade '{grade}'."


def load_reference_materials() -> str:
    """
    Load the handwriting reference materials from file.

    Returns:
        str: The contents of handwriting_reference.md
    """
    try:
        return REFERENCE_MATERIALS_PATH.read_text()
    except FileNotFoundError:
        return "ERROR: Reference materials not found. Please ensure handwriting_reference.md exists."


def get_handwriting_generator_prompt(
    grade: str,
    letter: str,
    student_level: str,
) -> str:
    """
    Fetch and compile the handwriting generator prompt.

    Combines:
    1. Langfuse prompt (or default if unavailable)
    2. Reference materials from local file
    3. Parameter substitution for grade, letter, student_level

    Args:
        grade: Grade level (PreK, K, 1st)
        letter: Target letter (A-Z)
        student_level: Student ability level (struggling, on-level, advanced)

    Returns:
        str: The complete system prompt with reference materials
    """
    client = get_langfuse_client()

    # Try to get prompt from Langfuse (skip if FORCE_LOCAL_PROMPT is set)
    base_prompt = None
    if client is not None and not os.getenv("FORCE_LOCAL_PROMPT"):
        try:
            prompt = client.get_prompt(LANGFUSE_PROMPT_NAME, label=LANGFUSE_PROMPT_LABEL)
            base_prompt = prompt.compile()
        except Exception:
            pass

    # Fall back to default if Langfuse unavailable
    if base_prompt is None:
        base_prompt = DEFAULT_HANDWRITING_GENERATOR_PROMPT

    # Load reference materials and grade-specific standards
    reference_materials = load_reference_materials()
    grade_standards = load_grade_standards(grade)

    # Substitute parameters
    return base_prompt.format(
        grade=grade,
        letter=letter.upper(),
        student_level=student_level,
        reference_materials=reference_materials,
        grade_standards=grade_standards,
    )


# --- Tool Definition ---


@tool
def finalize_lesson() -> str:
    """
    Signal that the lesson is complete and the user is satisfied.

    Call this tool when:
    - User explicitly approves the lesson ("looks good", "perfect", etc.)
    - User says they're done or satisfied
    - User thanks you without requesting changes

    This will end the lesson generation conversation.
    """
    return "Lesson finalized. The lesson generation is complete."


# Tool list for the agent
GENERATOR_TOOLS = [finalize_lesson]

# Tool name for state extraction
FINALIZE_TOOL_NAME = "finalize_lesson"


def create_handwriting_generator_agent(
    grade: str,
    letter: str,
    student_level: str,
    recursion_limit: int = 10,
):
    """
    Create the handwriting generator ReAct agent.

    Args:
        grade: Grade level for the lesson
        letter: Target letter for the lesson
        student_level: Student ability level for differentiation
        recursion_limit: Maximum number of agent turns

    Returns:
        CompiledStateGraph: The compiled ReAct agent
    """
    # Get model from registry
    model = get_chat_model("gpt-4o")

    # Get prompt with parameters and reference materials
    system_prompt = get_handwriting_generator_prompt(
        grade=grade,
        letter=letter,
        student_level=student_level,
    )

    # Create ReAct agent with finalize tool
    agent = create_agent(
        model=model,
        tools=GENERATOR_TOOLS,
        system_prompt=system_prompt,
    )

    return agent
