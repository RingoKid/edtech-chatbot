"""
Handwriting Generator Agent - ReAct agent for generating handwriting lessons.

Uses create_agent from langchain.agents for conversational lesson generation.
The agent generates lessons following the L4C methodology and can iterate
based on user feedback before finalizing.
"""

from pathlib import Path
from typing import Optional

from langchain_core.tools import tool
from langchain.agents import create_agent

from app.llm.client import get_chat_model
from app.graph.state import ActivityPlan
from app.graph.utils.extractors import (
    extract_activity,
    extract_verbal_cues,
    extract_gesture,
    extract_grade_standards,
)

GENERATOR_MODEL = "gpt-5.1"

# Path to reference materials
REFERENCE_MATERIALS_DIR = Path(__file__).parent.parent.parent.parent / "prompt" / "reference_materials"
HANDWRITING_DIR = REFERENCE_MATERIALS_DIR / "handwriting"
STANDARDS_PATH = REFERENCE_MATERIALS_DIR / "handwriting-spelling-standards.md"

# Map grade parameter to section header in standards doc
GRADE_TO_STANDARDS_HEADER = {
    "PreK": "PreK",
    "K": "Kindergarten",
    "1st": "1st Grade",
}

# Map grade parameter to Form C file
GRADE_TO_FORM_C_FILE = {
    "PreK": "form-c-prek.md",
    "K": "form-c-k.md",
    "1st": "form-c-1st.md",
}

# Universal form files loaded for every grade (Form C inserted at runtime)
# Form D removed (replaced by activity plan)
# Form F/G loaded in filtered form (target letter/sound only)
# Form H lazy-loaded on modification requests only
UNIVERSAL_FORM_FILES = [
    "training-codes.md",
    "form-b-lesson-structure.md",
    "form-a-objectives.md",
    # Form C inserted here at runtime (position 3)
    "form-e-best-practices.md",
]

# Paths for filtered extraction
FRAMEWORK_PATH = HANDWRITING_DIR / "activity-framework.md"
FORM_F_PATH = HANDWRITING_DIR / "form-f-verbal-cues.md"
FORM_G_PATH = HANDWRITING_DIR / "form-g-phoneme-gestures.md"
FORM_H_PATH = HANDWRITING_DIR / "form-h-modifications.md"


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

1. **Verbatim Explanations**: Each section's 💡 **Explanation:** text MUST be copied EXACTLY from Form B in the reference materials. Do not paraphrase or modify these explanations.

2. **Verbal Cues**: The ✏️ **Verbal Cues:** for the target letter are provided below. Use them EXACTLY as shown — do not look them up elsewhere.

3. **Activity Selection**: Follow the Activity Plan below. Each lesson section has a pre-selected activity.
   - **Name every activity exactly as shown** in the teacher script (e.g., "Let's play Sound Spark", "Time for Magic Finger Write"). Do NOT describe activities generically.
   - **Every section** (1-4) MUST use the planned activity.
   - **Materials section** MUST list all planned activities by name.

4. **Notation Conventions** (MUST use these exactly):
   - 💡 **Explanation:** → AI explains the parts of the lesson
   - 🗣️ **Teacher:** → What the teacher says (teacher dialogue)
   - 💬 **Child Response:** → Expected student responses
   - 👉 **Teacher Does:** → Teacher actions and demonstrations
   - 🤚 **Gesture:** → Phoneme gesture
   - ✏️ **Verbal Cues:** → Letter formation verbal cues
   - 🔄 **Adaptation:** → End-of-lesson modification prompt

5. **Complete Structure**: Your output MUST include ALL of these sections:
   - A. Standards (from the Grade-Specific Standards Reference below)
     - **PreK**: Use GELDS codes (CLL prefix). Select 1–3 standards that align with the lesson objectives.
     - **K**: Use Georgia K-12 ELA codes (K.F.* format). Include at least 4 standards, one from each category: Phonemic Awareness, Phoneme-Grapheme Correspondence, Encoding, Handwriting.
     - **1st**: Use Georgia K-12 ELA codes (1.F.* format). Include at least 4 standards, one from each category: Phonemic Awareness, Phoneme-Grapheme Correspondence, Encoding, Handwriting.
   - B. Objectives (scaffolded objectives)
   - C. Materials (list of materials)
   - D. Scripted Lesson Plan:
     1. Review & Connect
     2. Model, Explain & Engage
     3. Guided Practice
     4. Application
     5. Wrap-Up

6. **End with Modification Prompt**: Always end with:
   🔄 **Adaptation:** Let me know if you would like any modifications to the lesson

## INSTRUCTIONAL QUALITY RULES

7. **Think-Aloud Before Application**: Before students do the Application task (Section 4) independently, you MUST include a full teacher think-aloud worked example using a specific word. Detailed modeling is not just demonstrating directions — it is detailing what is happening in the thinking process to complete a task. The teacher must narrate the internal reasoning step by step. Example pattern:
   🗣️ **Teacher:** Let me show you. My turn. The word is cab. So, I first stretch the sounds, c-a-b, the beginning sound is /c/. I know that the /c/ sound is written with the letter c. I am going to write c in the first block. So, we have /c/-/a/. The /a/ sound is written with the letter a, so I write the letter a, remember that's our vowel, in the middle box. So, we have /c/-/a/-/b/. That's our new sound at the end. I am going to write the letter b for the /b/ sound in the last box. Okay. Let's try.

8. **Corrective Feedback**: Include at least 2 corrective feedback blocks in the lesson that anticipate specific, plausible student errors. Each block MUST: (a) name a specific likely error for the target letter/sound (e.g., confusing letter direction, confusing voiced/unvoiced pair, incorrect stroke sequence), (b) provide exact scripted teacher dialogue that explains the difference, and (c) engage students in noticing and fixing it. Example pattern:
   Corrective Feedback: Some children may confuse the direction of d, writing instead b or p.
   🗣️ **Teacher:** You are close. My sound is /d/. Everyone look up here. Some of you wrote this.
   👉 **Teacher Does:** Teacher writes b.
   🗣️ **Teacher:** This was our new sound we learned yesterday. This sound is /b/. We are writing /d/. This is /d/.
   👉 **Teacher Does:** Teacher writes d on the board.
   🗣️ **Teacher:** What is different about these two letters? Everyone think. Partner 1 tell Partner 2. Stop. Partner 2 tell Partner 1. Stop. Jesslyn, what is different about the /b/ and /d/?
   💬 **Child Response:** Child should respond that bottom bubble is different.
   🗣️ **Teacher:** Exactly, both the /d/ and /b/ have a straight line down, but one has a bubble on the back, the left, and one has a bubble in the front, on the right. Everyone say /d/. Where's the bubble, on the front or back? Everyone.
   💬 **Child Response:** On the back.
   🗣️ **Teacher:** Everyone say /b/. Where's the bubble? Everyone.
   💬 **Child Response:** On the front.

9. **Post-Response Explanations**: After the first and/or second elicited student response during an activity, the teacher MUST explain WHY the answer is correct — not just confirm it with "Yes!" or "Perfect!" or move on. The explanation should connect the student's answer to the underlying concept. Example pattern:
   🗣️ **Teacher:** Does /b/-et start with the /b/ or /p/ sound?
   💬 **Child Response:** Children should say /b/.
   🗣️ **Teacher:** Yes. I am pushing out air and using my vocal box /b/, so I am going to hold up my ball sound card for the /b/ sound.

10. **Sound/Letter Comparison with Confusable Partner**: In Section 2 (Model, Explain & Engage), include a compare/contrast between the target sound/letter and its most commonly confused partner. You MUST: state what is similar, state what is different, include articulatory detail (mouth, lips, tongue, voicing), and have students produce both sounds. Example pattern:
   🗣️ **Teacher:** Remember that we said that the /{letter}/ sound is a lot like the [confusable] sound.
   🗣️ **Teacher:** Look at my mouth and listen to the sound of each one.
   🗣️ **Teacher:** Ready. /{letter}/
   🗣️ **Teacher:** Ready. [confusable]
   🗣️ **Teacher:** What's different?
   💬 **Child Response:** Children should respond with the key difference.
   🗣️ **Teacher:** Right. For the /{letter}/ sound, [articulatory description]. For the [confusable] sound, [articulatory description].
   🗣️ **Teacher:** Everyone put your hand on your vocal box and make the /{letter}/ sound. Everyone.
   🗣️ **Teacher:** Now let's make the [confusable] sound. Everyone.

11. **Verbatim Teacher Script — Not Stage Directions**: Write the EXACT words the teacher will say. Do NOT write stage directions that require teacher improvisation. Every section must have verbatim read-aloud teacher dialogue.
   - BAD: "👉 **Teacher Does:** Teacher demonstrates writing and uses sequence verbal cues"
   - GOOD: "🗣️ **Teacher:** Watch me. I'm going to write uppercase {letter}. [verbal cues from Form F]."
   - BAD: "👉 **Teacher Does:** Teacher continues this process with remaining words"
   - GOOD: Script out at least 2-3 full cycles with specific words.
   - Include pacing cues in EVERY section: "Ready... Go", "My turn... Your turn", "Say it with me", "Get Ready Go."
   - Include specific example words (at least 2-3) in Sound Hunt and Application activities — do not leave word lists to the teacher.
   - Script specific child responses with 💬 **Child Response:**, not generic "💬 **Child Response:** Children respond".

12. **Prior Practice Awareness**: The student has learned these sounds: {previously_learned}. Use ONLY these sounds plus the target sound when selecting example words. Do not use words that contain sounds not in this list. If the list is empty, this is the student's first lesson — use only the target sound.

## GRADE-LEVEL DELIVERY RULES

These rules override general instructions when they conflict. Always check the current grade level ("{grade}") before writing each section.

13. **Letter Case**:
   - PreK: Teach LOWERCASE only by default. Uppercase is an optional extension a teacher can request.
   - K: Teach lowercase first, then uppercase. Both cases are taught.
   - 1st: Both cases, but no explicit formation teaching needed — focus on fluency.

14. **Directionality Instruction** (left-to-right, top/middle/bottom lines):
   - PreK: ALWAYS explicitly teach — left-to-right movement, name the top/middle/bottom lines before modeling the letter.
   - K: Brief reminders only, not full instruction (unless student is struggling).
   - 1st: Do NOT include directionality instruction.

15. **Mouth Placement / Articulation**:
   - PreK: ALWAYS include explicit mouth/lip/tongue/vocal box instruction for the target sound in Section 2.
   - K: Include if the sound is new or commonly confused.
   - 1st: Do NOT include — students learned this in PreK/K. Jump straight to the sound activity.

16. **Guided Practice Techniques**:
   - PreK: Use finger tracing (Magic Finger Write) BEFORE pencil. Then dotted-line tracing (Trace & Say). Sequence: finger → trace → write.
   - K: Magic Finger Write appropriate. Tracing for struggling/on-level. Advanced can skip to Say and Write.
   - 1st: Do NOT use Magic Finger Write or dotted-line tracing. Use memory-based practice (Disappearing Letter, Cover & Try) or Say and Write. Count strokes or say sequence instead of finger tracing.

17. **Content Scope**:
   - PreK: Individual sound/letter focus. Sound isolation = beginning sounds only. Application = write single letters.
   - K: Letter within CVC word context. Sound isolation = beginning AND ending sounds. Application = spell CVC words.
   - 1st: Spelling patterns (CVCe, digraphs, etc.). Sound isolation = medial vowels. Application = spell full words, distinguish patterns.

18. **Prior Knowledge & Scaffolding Intensity**:
   - PreK: Teach from scratch. Heavy scaffolding. "My turn first" before every new step. Multiple repetitions.
   - K: Some sound knowledge assumed. Moderate scaffolding.
   - 1st: All consonant/vowel sounds and graphemes already known. Light scaffolding. Students can do more independently.

19. **Image Placeholders**: Place EXACTLY 3 image placeholders in your lesson using this syntax:
   `![2-3 sentence description of the image focused on pedagogical content](IMAGE_N)`
   where N is 1, 2, or 3. Placement guidance:
   - `IMAGE_1` → in Section 2 (Model, Explain & Engage)
   - `IMAGE_2` → in Section 3 (Guided Practice)
   - `IMAGE_3` → in Section 4 (Application)
   The description should focus on what the image teaches (e.g., "Step-by-step formation guide for lowercase letter d showing numbered stroke order with a starting dot and directional arrows on writing lines."). Do NOT include image-model boilerplate like "white background" or "children's book style" — just describe the pedagogical content.

## After Generating

After presenting the lesson:
- If the user requests modifications, regenerate the lesson incorporating their feedback
- If the user approves the lesson (says "looks good", "thanks", "done", etc.), call the `finalize_lesson` tool

## Output Format

Generate the lesson in clean markdown format following the Form C example for your grade level.

---

## Skill Focus

The primary skill to develop in this lesson is: **{skill_focus}**

---

## Activity Plan

{activity_plan_section}

---

## Verbal Cues (Letter {letter})

{verbal_cues}

---

## Phoneme Gesture

{phoneme_gesture}

---

## Grade-Specific Standards Reference

{grade_standards}

---

## Reference Materials

{reference_materials}
"""



def load_universal_materials(grade: str) -> str:
    """
    Load universal reference materials (Forms A, B, C, E).

    These are always included regardless of activity selection.
    """
    form_c_file = GRADE_TO_FORM_C_FILE.get(grade)
    if not form_c_file:
        return f"ERROR: Unknown grade '{grade}'."

    # Build file list with Form C inserted at position 3
    files = list(UNIVERSAL_FORM_FILES)
    files.insert(3, form_c_file)

    parts = []
    for filename in files:
        path = HANDWRITING_DIR / filename
        try:
            parts.append(path.read_text().strip())
        except FileNotFoundError:
            parts.append(f"ERROR: {filename} not found.")

    return "\n\n---\n\n".join(parts)


def _slug_to_display_name(framework: str, slug: str) -> str:
    """Extract display name from framework heading: ### [slug] Display Name."""
    import re
    pattern = rf"^### \[{re.escape(slug)}\] (.+)$"
    match = re.search(pattern, framework, re.MULTILINE)
    return match.group(1).strip() if match else slug


def build_activity_plan_section(activity_plan: Optional[ActivityPlan]) -> str:
    """Build the activity plan section with extracted descriptions."""
    if not activity_plan:
        return "(No activity plan provided — select activities based on student level.)"

    try:
        framework = FRAMEWORK_PATH.read_text()
    except FileNotFoundError:
        return "ERROR: Activity framework not found."

    sections = []
    plan_fields = [
        ("Review", "review"),
        ("Sound Target Focus", "sound_target"),
        ("Handwriting Focus", "handwriting"),
        ("Spelling Focus", "spelling"),
    ]

    for section_name, field in plan_fields:
        slug = activity_plan[field]
        display_name = _slug_to_display_name(framework, slug)
        description = extract_activity(framework, slug)
        sections.append(f"### {section_name}: {display_name}\n\n{description}")

    if activity_plan.get("handwriting_chain"):
        chain_slug = activity_plan["handwriting_chain"]
        chain_name = _slug_to_display_name(framework, chain_slug)
        chain_desc = extract_activity(framework, chain_slug)
        sections.append(
            f"### Handwriting Chain (rehearsal\u2192writing): {chain_name}\n\n{chain_desc}"
        )

    if activity_plan.get("standards"):
        standards_str = ", ".join(activity_plan["standards"])
        sections.append(f"### Standards\n\n{standards_str}")

    return "\n\n".join(sections)


def get_handwriting_generator_prompt(
    grade: str,
    letter: str,
    student_level: str,
    previously_learned: Optional[list[str]] = None,
    skill_focus: str = "isolating_sounds",
    activity_plan: Optional[ActivityPlan] = None,
    is_modification: bool = False,
) -> str:
    """
    Compile the handwriting generator prompt with filtered materials.

    Uses the activity plan to include only relevant reference content:
    - Universal forms (A, B, C, E)
    - Filtered Form F (target letter only)
    - Filtered Form G (target sound only)
    - Selected activity descriptions from framework
    - Grade-specific standards
    - Form H (modification examples) — only when is_modification=True
    """
    if previously_learned is None:
        previously_learned = []

    # Universal materials (Forms A, B, C, E) + Form H on modifications
    reference_materials = load_universal_materials(grade)

    if is_modification:
        try:
            form_h = FORM_H_PATH.read_text().strip()
            reference_materials += "\n\n---\n\n" + form_h
        except FileNotFoundError:
            pass  # Form H missing is non-fatal

    # Grade-specific standards via regex extraction
    try:
        standards_content = STANDARDS_PATH.read_text()
    except FileNotFoundError:
        standards_content = ""
    header_key = GRADE_TO_STANDARDS_HEADER.get(grade, grade)
    grade_standards = extract_grade_standards(standards_content, header_key)

    # Filtered verbal cues (target letter only)
    try:
        form_f_content = FORM_F_PATH.read_text()
    except FileNotFoundError:
        form_f_content = ""
    verbal_cues = extract_verbal_cues(form_f_content, letter)

    # Filtered phoneme gesture (target sound only)
    try:
        form_g_content = FORM_G_PATH.read_text()
    except FileNotFoundError:
        form_g_content = ""
    phoneme_gesture = extract_gesture(form_g_content, letter)

    # Activity plan with descriptions
    activity_plan_section = build_activity_plan_section(activity_plan)

    # Previously learned sounds
    learned_str = ", ".join(previously_learned) if previously_learned else "(none — first lesson)"

    return DEFAULT_HANDWRITING_GENERATOR_PROMPT.format(
        grade=grade,
        letter=letter.upper(),
        student_level=student_level,
        previously_learned=learned_str,
        skill_focus=skill_focus,
        reference_materials=reference_materials,
        grade_standards=grade_standards,
        verbal_cues=verbal_cues,
        phoneme_gesture=phoneme_gesture,
        activity_plan_section=activity_plan_section,
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
    previously_learned: Optional[list[str]] = None,
    skill_focus: str = "isolating_sounds",
    activity_plan: Optional[ActivityPlan] = None,
    is_modification: bool = False,
    recursion_limit: int = 10,
):
    """
    Create the handwriting generator ReAct agent.

    Args:
        grade: Grade level for the lesson
        letter: Target letter for the lesson
        student_level: Student ability level for differentiation
        previously_learned: Sounds/letters already taught
        skill_focus: Primary skill to target
        activity_plan: Pre-selected activities from the planner
        recursion_limit: Maximum number of agent turns

    Returns:
        CompiledStateGraph: The compiled ReAct agent
    """
    # Get model from registry (streaming keeps TCP alive, prevents VPN/proxy idle drops)
    model = get_chat_model(GENERATOR_MODEL, streaming=True)

    # Get prompt with parameters and filtered reference materials
    system_prompt = get_handwriting_generator_prompt(
        grade=grade,
        letter=letter.upper(),
        student_level=student_level,
        previously_learned=previously_learned,
        skill_focus=skill_focus,
        activity_plan=activity_plan,
        is_modification=is_modification,
    )

    # Create ReAct agent with finalize tool
    agent = create_agent(
        model=model,
        tools=GENERATOR_TOOLS,
        system_prompt=system_prompt,
    )

    return agent
