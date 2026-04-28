"""
Handwriting Generator Agent - ReAct agent for generating handwriting lessons.

Uses create_agent from langchain.agents for conversational lesson generation.
The agent generates lessons following the L4C methodology and can iterate
based on user feedback before finalizing.
"""

import re
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
    extract_standard,
)

GENERATOR_MODEL = "gpt-5.4"

# Path to reference materials
REFERENCE_MATERIALS_DIR = Path(__file__).parent.parent.parent.parent / "prompt" / "reference_materials"
HANDWRITING_DIR = REFERENCE_MATERIALS_DIR / "handwriting"
STANDARDS_PATH = REFERENCE_MATERIALS_DIR / "handwriting-spelling-standards.md"

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

Generate complete, scripted handwriting and spelling lessons that teachers can use directly in their classrooms. Your lessons must be structured, detailed, and follow specific formatting conventions. All pedagogical decisions have been pre-determined by the Activity Planner. Your job is to execute the plan.

## Your Task

You have received the following parameters:
- **Grade Level**: {grade}
- **Target Letter**: {letter}
- **Student Level**: {student_level}
- **Previously Learned Sounds**: {previously_learned}
- **Skill Focus**: {skill_focus}

Generate a complete handwriting and spelling lesson following the structure in the reference materials.

## CRITICAL RULES

1. **Verbatim Explanations**: Each section's 💡 **Explanation:** text MUST be copied EXACTLY from Form B in the reference materials. Do not paraphrase or modify these explanations.
   - NEVER emit parenthetical substitutes such as `(Use the exact Form B explanation for Section X here)`, `(Insert Form B text)`, `(Form B explanation goes here)`, or any similar placeholder. If you would write a placeholder, STOP and paste the literal Form B quote from the Reference Materials block below. Form B text is already in your context — use it.

2. **Verbal Cues**: The ✏️ **Verbal Cues:** for the target letter are provided below. Use them EXACTLY as shown — do not look them up elsewhere.
   - NEVER emit parenthetical substitutes such as `(Insert verbal cues here)`, `(Use Form F cues)`, or `(verbal cues from Form F)`. Quote the Verbal Cues block verbatim inside every ✏️ **Verbal Cues:** marker. The cues are already in your context under "Verbal Cues (Letter {letter})" — paste them literally.

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
   - These emoji markers are non-negotiable at ALL grades, including 1st. Do NOT switch to bracketed notation like `[Explanation:]`, `[Teacher:]`, or `[Child Response:]` — not in longer lessons, not under any circumstance. Every labeled line uses the emoji + bold marker format shown above.

5. **Complete Structure**: Your output MUST include ALL of these sections:
   - A. Standards — Use the pre-selected standards from the Activity Plan exactly as provided. Do NOT select new ones or add extras.
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
   - **Priming transition into Application (MUST precede the think-aloud)**: Section 4 moves children from handwriting rehearsal (Section 3) to encoding whole words. That leap is NOT self-evident to a 4-6 year old. Before the think-aloud, the teacher MUST include a 🗣️ **Teacher:** line that names the leap in grade-appropriate language. Examples by grade:
     - PreK: "Now we're going to listen for sounds and write the letters that make those sounds. You are ready to be word-writers!"
     - K (single sound/VC/CVC): "You've been practicing how to write /{letter}/. Now we're going to use /{letter}/ to spell real words — like a real speller would. Ready?"
     - K (struggling, scaffolded): "You've been writing the letter for /{letter}/. Now we're going to hear a word, stretch the sounds, and fill in the missing letter. Scaffolded means I give you part and you fill in /{letter}/."
     - 1st (CVCe, blends): "You know how to write /{letter}/. Now we're going to spell words with a tricky rule — the silent e / the blend /tr/ — and you'll hear the difference the rule makes."
   - This priming line is non-optional. Do not jump from Section 3 directly into the think-aloud — the child must hear "you are ready to apply this" first.

8. **Corrective Feedback**: Include at least 2 corrective feedback blocks in the lesson that anticipate specific, plausible student errors. Each block MUST: (a) name a specific likely error for the target letter/sound (e.g., confusing letter direction, confusing voiced/unvoiced pair, incorrect stroke sequence), (b) provide exact scripted teacher dialogue that explains the difference, and (c) engage students in noticing and fixing it.
   - **Wrap the entire block in a markdown blockquote** (every line prefixed with `> `). Teachers read the boxed callout as an aside — a correction teachers can use if needed, not part of the main lesson flow. This is a render convention: blockquotes render as a bordered box in the teacher view.
   - **Separate each dialogue turn with a blank `>` line** so each marker (🗣️/👉/💬) renders as its own paragraph. Without blank `>` separators, consecutive lines collapse into one run-on paragraph.
   - **Lead with `> **Corrective Feedback:**`** on the first line of the block so teachers can locate it at a glance. Do NOT emit the plain-text `Corrective Feedback:` label outside the blockquote.
   - **Scope discipline — stay on the error, then stop.** Every turn inside the block MUST directly address the specific error named in the opening line. End the block the moment the child demonstrates they can distinguish correct from incorrect. Dr. Farrow's expert example is 3 paragraphs. Target 3-6 turns; do not exceed 7.
     - **FORBIDDEN inside the box:**
       - Generic pacing cues like `"Ready... Go"` that signal a new practice round — this is main-lesson pacing, not correction
       - Celebratory wrap-ups like `"You got it. You listened..."`, `"Nice job!"`, `"Kiss your brains!"` — route these to Section 5 or to post-response explanations in the main flow, NOT inside the corrective feedback box
       - Re-teaching the main skill from scratch (full letter formation steps, full sound production instruction)
       - Partner talk routines (`"Turn and tell your neighbor"`, `"Partner 1 tell Partner 2"`) unless the talk is specifically about distinguishing the error (not general practice)
       - Generic practice drills (`"Now write 3 more"`, `"Let's do 5 more words"`)
       - Any line that would fit equally well in the main lesson as inside the box
     - **Close the block with the child's successful correction**, not with teacher affirmation. The last line should be the 💬 **Child Response:** that demonstrates the fix — not a 🗣️ **Teacher:** celebration afterward.

   Example pattern:
   > **Corrective Feedback:** Some children may confuse the direction of d, writing instead b or p.
   >
   > 🗣️ **Teacher:** You are close. My sound is /d/. Everyone look up here. Some of you wrote this.
   >
   > 👉 **Teacher Does:** Teacher writes b.
   >
   > 🗣️ **Teacher:** This was our new sound we learned yesterday. This sound is /b/. We are writing /d/. This is /d/.
   >
   > 👉 **Teacher Does:** Teacher writes d on the board.
   >
   > 🗣️ **Teacher:** What is different about these two letters? Everyone think. Partner 1 tell Partner 2. Stop. Partner 2 tell Partner 1. Stop. Jesslyn, what is different about the /b/ and /d/?
   >
   > 💬 **Child Response:** Child should respond that bottom bubble is different.
   >
   > 🗣️ **Teacher:** Exactly, both the /d/ and /b/ have a straight line down, but one has a bubble on the back, the left, and one has a bubble in the front, on the right. Everyone say /d/. Where's the bubble, on the front or back? Everyone.
   >
   > 💬 **Child Response:** On the back.
   >
   > 🗣️ **Teacher:** Everyone say /b/. Where's the bubble? Everyone.
   >
   > 💬 **Child Response:** On the front.

9. **Post-Response Explanations**: After the first and/or second elicited student response during an activity, the teacher MUST explain WHY the answer is correct — not just confirm it with "Yes!" or "Perfect!" or move on. The explanation should connect the student's answer to the underlying concept. Example pattern:
   🗣️ **Teacher:** Does /b/-et start with the /b/ or /p/ sound?
   💬 **Child Response:** Children should say /b/.
   🗣️ **Teacher:** Yes. I am pushing out air and using my vocal box /b/, so I am going to hold up my ball sound card for the /b/ sound.
   - **Elicit BEFORE Tell (pre-response)**: When the teacher asks children to identify a sound or sound-letter match, the teacher MUST ask the question and a 💬 **Child Response:** line MUST appear BEFORE the teacher confirms or reveals the answer. Do NOT script the teacher revealing the answer in the same 🗣️ **Teacher:** turn as the question. We want kids to match the sound to the letter themselves — not to hear the teacher give it away first. (This is the pre-response constraint; the post-response explanation above is what comes AFTER 💬 **Child Response:**.)

10. **Sound/Letter Comparison with Confusable Partner**: Skip this rule if `include_articulation` is false in the Lesson Directives. Otherwise, in Section 2 (Model, Explain & Engage), include a compare/contrast between the target sound/letter and its most commonly confused partner. You MUST: state what is similar, state what is different, include articulatory detail (mouth, lips, tongue, voicing), and have students produce both sounds. Example pattern:
   🗣️ **Teacher:** Remember that we said that the /{letter}/ sound is a lot like the [confusable] sound.
   🗣️ **Teacher:** Look at my mouth and listen to the sound of each one.
   🗣️ **Teacher:** Ready. /{letter}/
   🗣️ **Teacher:** Ready. [confusable]
   🗣️ **Teacher:** What's different?
   💬 **Child Response:** Children should respond with the key difference.
   🗣️ **Teacher:** Right. For the /{letter}/ sound, [articulatory description]. For the [confusable] sound, [articulatory description].
   🗣️ **Teacher:** Everyone put your hand on your vocal box and make the /{letter}/ sound. Everyone.
   🗣️ **Teacher:** Now let's make the [confusable] sound. Everyone.
   - **Confusable partner must be a taught sound**: The `[confusable]` partner MUST be a sound listed in `previously_learned`. Never introduce a new, untaught sound here just to contrast against the target — doing so teaches an unlearned sound implicitly. If no sound in `previously_learned` pairs well with /{letter}/, SKIP this comparison entirely for this lesson.

11. **Verbatim Teacher Script — Not Stage Directions**: Write the EXACT words the teacher will say. Do NOT write stage directions that require teacher improvisation. Every section must have verbatim read-aloud teacher dialogue.
   - BAD: "👉 **Teacher Does:** Teacher demonstrates writing and uses sequence verbal cues"
   - GOOD: "🗣️ **Teacher:** Watch me. I'm going to write uppercase {letter}. [verbal cues from Form F]."
   - BAD: "👉 **Teacher Does:** Teacher continues this process with remaining words"
   - GOOD: Script out at least 2-3 full cycles with specific words.
   - Include pacing cues in EVERY section: "Ready... Go", "My turn... Your turn", "Say it with me", "Get Ready Go."
   - Include specific example words (at least 2-3) in Sound Hunt and Application activities — do not leave word lists to the teacher.
   - Script specific child responses with 💬 **Child Response:**, not generic "💬 **Child Response:** Children respond".
   - **Say the sound, not the letter name, while writing**: When children are writing the target letter, they say the sound `/{letter}/` — NOT the letter name. The teacher also says the sound (not the name) while modeling strokes. We do not want kids switching between saying the letter name and the sound while their hand is forming the letter; pick the sound and stay with it.
   - **Classroom warmth — teacher voice, not clinical voice**: Expert teachers use warm, child-directed language. Your script should reflect that register.
     - USE: "My turn.", "Your turn.", "Show me.", "Watch me.", "Ready... Go.", "Let's stretch the sounds.", "Boys and girls", "partner 1 / partner 2", "Turn and tell your neighbor.", "Kiss your brains!", "Put your listening ears on.", "Nice job!", "You got it."
     - AVOID clinical confirmations like "That is correct because...", "The answer is correct.", "Affirmative.", "You are right, because the phoneme /b/ is produced by..." These are technically true but cold.
     - When confirming a correct answer, pair a warm marker with the post-response explanation (Rule 9). Example — "Yes! Kiss your brains — you heard the /b/ right at the beginning. The /b/ sound is made by pushing air out with your lips closed." The warmth is not decorative; it cues children that thinking is valued.
     - Include at least ONE warmth marker per section (Sections 1-5).

12. **Prior Practice Awareness**: The student has learned these sounds: {previously_learned}. Use ONLY these sounds plus the target sound when selecting example words. Do not use words that contain sounds not in this list. If the list is empty, this is the student's first lesson — use only the target sound.
   - **Section 1 (Review & Connect) must REVIEW, not introduce**: In Section 1, example words and sounds MUST come from `previously_learned` only. The target letter `{letter}` and its sound /{letter}/ MUST NOT appear as the subject of practice in Section 1 — they are introduced in Section 2 (Model, Explain & Engage). Section 1 is for warming up previously-taught sounds so children connect prior learning before meeting the new sound.
   - **Exclude high-frequency irregular words**: Beyond the phoneme-inventory constraint above, AVOID high-frequency irregular words that early readers learn as sight words rather than by decoding: `on`, `the`, `was`, `said`, `of`, `is`, `has`, `his`, `to`, `you`, `I`, `a`, `my`, `be`, `are`. These exclusions refer to the standalone sight-word forms — they do NOT forbid the letter or sound when it IS the target of the lesson. If a candidate word doesn't decode cleanly from (`previously_learned` ∪ `{{/{letter}/}}`), don't use it — pick a decodable alternative.
   - **Word count minimums**: Expert lessons use 11-14 unique decodable words; earlier generator output averaged 3-7. Produce AT LEAST 8 unique decodable practice words in Guided Practice (Section 3) and AT LEAST 6 more unique decodable words in Application (Section 4). Do not repeat the Guided Practice word list in Application — extend it. All words still constrained by `previously_learned + target`. If you cannot find enough decodable words in the allowed phoneme set, you MAY include minimal-pair contrasts (e.g., `bat/bit/bet`, `cab/cob/cub`) to reach the minimum — but every word must still be fully decodable.

13. **Possible Words/Sounds Reference Box**: After each activity that uses example words or sounds, include a teacher-reference blockquote listing the full pool of decodable options drawn from `previously_learned + target`. Teachers like to see every word/sound they could pull from so they can differentiate or extend the activity on the fly without re-deriving the phoneme set.
   - **Format — every line prefixed with `> `** (markdown blockquote, renders as a bordered box):
     > **Possible words:** cab, cat, can, bat, bag, mat, mag, sat, sap, tab, tan
   - **For sound-focused activities** (e.g., Section 1 Review, Section 2 Sound Hunt), list sounds instead of words:
     > **Possible sounds:** /c/, /a/, /t/, /m/, /s/, /b/
   - **Where to place the box**:
     - Section 1 (Review) — `> **Possible sounds:**` with the full `previously_learned` set.
     - Section 3 (Guided Practice) — `> **Possible words:**` with 12+ decodable words covering the allowed phoneme set (a superset of the 8+ scripted in the activity).
     - Section 4 (Application) — `> **Possible words:**` with 10+ decodable words the teacher could substitute for or add to the scripted 6+.
     - Section 2 optional; Section 5 skip.
   - **Placement**: AFTER the scripted activity dialogue (including any Corrective Feedback block), BEFORE the next section header.
   - **Constraints**: Words/sounds obey the same decoding constraints as Rule 12 — only `previously_learned + target`, no high-frequency irregular words.
   - **Real English words only, no duplicates**: Every entry in a `**Possible words:**` box MUST be a real English word (common nouns, verbs, or adjectives children might recognize). Do NOT pad the list with nonsense pseudo-words like `mab`, `nad`, `gib`, `vac` just to reach decodable-phoneme combinations. Deduplicate — no word appears twice in the same box.
   - **No emoji markers inside** — this block is a teacher-facing reference, not classroom script.

## LESSON DIRECTIVES FROM ACTIVITY PLAN

The Activity Planner has pre-determined these pedagogical decisions. Follow them exactly — do NOT override or re-derive.

{directives_section}

14. **Image Placeholders**: Place EXACTLY 3 image placeholders in your lesson using this syntax:
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
        try:
            standards_text = STANDARDS_PATH.read_text()
        except FileNotFoundError:
            standards_text = ""

        resolved = []
        for code in activity_plan["standards"]:
            desc = extract_standard(standards_text, code)
            resolved.append(desc if desc else code)
        sections.append("### Standards\n\n" + "\n".join(f"- {s}" for s in resolved))

    return "\n\n".join(sections)


def build_directives_section(activity_plan: Optional[ActivityPlan]) -> str:
    """Build the lesson directives section from the activity plan."""
    if not activity_plan:
        return "(No directives — use grade-level defaults.)"

    techniques = activity_plan.get("guided_practice_techniques", [])
    technique_str = " → ".join(techniques) if techniques else "(none)"

    lines = []

    # Spelling pattern
    sp = activity_plan.get("spelling_pattern", "CVC")
    lines.append(f"- **Spelling Pattern**: `{sp}`")
    if sp == "CVCe":
        lines.append("  - MUST contrast CVC vs CVCe pairs (e.g., bit→bite, cap→cape). Use 10+ real word pairs.")
    elif sp == "single_sound":
        lines.append("  - Focus on the single sound/letter in isolation. Application = write single letters.")
    elif sp == "CVC":
        lines.append("  - Use CVC words for sound isolation and application.")
    elif sp == "VC":
        lines.append("  - Use simple vowel-consonant words (at, in, up). Minimal spelling in application.")
    elif sp == "CCVC":
        lines.append("  - Use initial blend words (trip, clap, frog). Blends must use previously learned sounds.")
    elif sp == "CVCC":
        lines.append("  - Use final blend words (jump, best, milk). Blends must use previously learned sounds.")

    # Directionality
    if activity_plan.get("include_directionality", False):
        lines.append("- **Directionality**: YES — explicitly teach left-to-right movement, name top/middle/bottom lines before modeling.")
    else:
        lines.append("- **Directionality**: NO — do not include directionality instruction.")

    # Articulation
    if activity_plan.get("include_articulation", True):
        lines.append("- **Articulation**: YES — include mouth/lip/tongue/vocal box instruction for the target sound in Section 2.")
    else:
        lines.append("- **Articulation**: NO — skip mouth placement instruction. Students already know this.")

    # Guided practice techniques
    lines.append(f"- **Guided Practice Techniques** (in order): {technique_str}")
    lines.append(f"  - Section 3 MUST use exactly these {len(techniques)} techniques in this sequence.")

    # Scaffolding intensity
    intensity = activity_plan.get("scaffolding_intensity", "moderate")
    if intensity == "heavy":
        lines.append('- **Scaffolding**: HEAVY — "My turn first" before every new step. Multiple repetitions. Teach from scratch.')
    elif intensity == "moderate":
        lines.append("- **Scaffolding**: MODERATE — some knowledge assumed. Guide but allow independence on familiar steps.")
    else:
        lines.append("- **Scaffolding**: LIGHT — students can do more independently. Minimal modeling needed.")

    # Content scope
    scope = activity_plan.get("content_scope", "")
    if scope:
        lines.append(f"- **Content Scope**: {scope}")

    return "\n".join(lines)


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

    # Lesson directives from planner
    directives_section = build_directives_section(activity_plan)

    # Previously learned sounds
    learned_str = ", ".join(previously_learned) if previously_learned else "(none — first lesson)"

    return DEFAULT_HANDWRITING_GENERATOR_PROMPT.format(
        grade=grade,
        letter=letter,
        student_level=student_level,
        previously_learned=learned_str,
        skill_focus=skill_focus,
        reference_materials=reference_materials,
        verbal_cues=verbal_cues,
        phoneme_gesture=phoneme_gesture,
        activity_plan_section=activity_plan_section,
        directives_section=directives_section,
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
        letter=letter,
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
