"""Pydantic models for structured LLM judge output in scaffolding evals."""

from pydantic import BaseModel, Field
from typing import Literal, Optional


# --- Within-Section Eval Models ---


class Activity(BaseModel):
    """A single activity identified within a lesson section."""

    name: str = Field(description="Name of the activity (e.g., 'Sound Sparks', 'Magic Finger Write')")
    difficulty_level: Literal["low", "middle", "high"] = Field(
        description="Difficulty level from Form D: low, middle, or high"
    )
    reasoning: str = Field(
        description="Why this difficulty level, referencing Form D activity descriptions"
    )


class ActivityPair(BaseModel):
    """A consecutive pair of activities within a section, evaluated for ordering."""

    from_activity: str = Field(description="Name of the earlier activity in the pair")
    to_activity: str = Field(description="Name of the later activity in the pair")
    correctly_ordered: bool = Field(
        description="True if the later activity is equal or harder difficulty than the earlier one"
    )
    reasoning: str = Field(description="Explanation of why this pair is or isn't correctly ordered")


class SectionAnalysis(BaseModel):
    """Analysis of activity sequencing within a single lesson section."""

    section_name: str = Field(
        description="Section name: 'Review & Connect', 'Model, Explain & Engage', 'Guided Practice', or 'Application'"
    )
    activities: list[Activity] = Field(description="All distinct activities/steps identified in this section")
    pairs: list[ActivityPair] = Field(
        description="All consecutive activity pairs evaluated for ordering"
    )


class WithinSectionOutput(BaseModel):
    """Complete structured output from the within-section scaffolding judge."""

    sections: list[SectionAnalysis] = Field(
        description="Analysis for sections 1-4 only (exclude Wrap-Up/section 5)"
    )
    explanation: str = Field(description="Overall summary of within-section sequencing quality")


# --- Across-Section Eval Models ---


class CrossSectionLink(BaseModel):
    """A dependency link between activities in different sections."""

    earlier_section: str = Field(description="Name of the earlier section (e.g., 'Model, Explain & Engage')")
    earlier_activity: str = Field(description="Name of the activity in the earlier section")
    later_section: str = Field(description="Name of the later section (e.g., 'Application')")
    later_activity: str = Field(description="Name of the activity in the later section")
    builds_correctly: bool = Field(
        description="True if the earlier activity genuinely primes/prepares skills for the later one"
    )
    reasoning: str = Field(
        description="How the earlier activity primes or builds toward the later one"
    )


class AcrossSectionOutput(BaseModel):
    """Complete structured output from the across-section scaffolding judge."""

    links: list[CrossSectionLink] = Field(
        description="All identified cross-section dependencies between activities in sections 1-4"
    )
    explanation: str = Field(description="Overall summary of across-section coherence")


# --- Gradual Release Eval Models ---


class SupportLevel(BaseModel):
    """Teacher support level for a section or step within the lesson."""

    section_or_step: str = Field(
        description="Section name (e.g., 'Model, Explain & Engage') or step name (e.g., 'Say and Trace')"
    )
    support_level: Literal["high", "medium", "low"] = Field(
        description="Overall teacher support level"
    )
    indicators: list[str] = Field(
        description="Concrete evidence from the script (e.g., \"teacher says 'My turn' before children attempt\")"
    )
    reasoning: str = Field(description="Why this support level was assigned")


class SupportTransition(BaseModel):
    """A transition between two sections or steps, evaluated for support decrease."""

    from_step: str = Field(description="Earlier section or step name")
    to_step: str = Field(description="Later section or step name")
    support_decreased: bool = Field(
        description="True if the later step has equal or less teacher support (accounting for cognitive load trade-offs)"
    )
    reasoning: str = Field(
        description="Explanation of the support change, including cognitive load considerations if applicable"
    )


class GradualReleaseOutput(BaseModel):
    """Complete structured output from the gradual release scaffolding judge."""

    across_section_levels: list[SupportLevel] = Field(
        description="One entry per section: 2, 3, 4"
    )
    across_section_transitions: list[SupportTransition] = Field(
        description="Section transitions: 2→3, 3→4"
    )
    within_section_levels: list[SupportLevel] = Field(
        description="Steps identified inside Section 3"
    )
    within_section_transitions: list[SupportTransition] = Field(
        description="Consecutive step pairs within Section 3"
    )
    explanation: str = Field(description="Overall summary of gradual release quality")


# --- Decomposition Eval Models ---


class ComponentSkill(BaseModel):
    """A component sub-skill required by a complex task."""

    skill_name: str = Field(
        description="Name of the component skill (e.g., 'sound segmentation')"
    )
    is_taught: bool = Field(
        description="Whether this skill is explicitly taught before the complex task"
    )
    taught_in_section: Optional[str] = Field(
        default=None,
        description="Section name where it's taught, or None if missing",
    )
    taught_via_activity: Optional[str] = Field(
        default=None,
        description="Activity name that teaches it, or None if missing",
    )
    reasoning: str = Field(
        description="What the sub-skill is and where/whether it appears"
    )


class ComplexTask(BaseModel):
    """A complex task in Sections 3-4 that requires multiple component skills."""

    task_name: str = Field(
        description="Name of the complex activity (e.g., 'Stretch and Spell')"
    )
    section: str = Field(
        description="Section where it appears (e.g., 'Application')"
    )
    required_components: list[ComponentSkill] = Field(
        description="All component sub-skills this task requires"
    )


class DecompositionOutput(BaseModel):
    """Complete structured output from the decomposition scaffolding judge."""

    complex_tasks: list[ComplexTask] = Field(
        description="All complex tasks identified in Sections 3-4"
    )
    explanation: str = Field(description="Overall summary of decomposition quality")


# --- Verbatim Explanations Eval Models ---


class VerbatimSection(BaseModel):
    """Evaluation of a single [Explanation] block against Form B verbatim text."""

    section_name: str = Field(description="e.g., 'Review & Connect'")
    found: bool = Field(description="Was an [Explanation] block found?")
    is_verbatim: bool = Field(description="Exact match to Form B?")
    actual_text: str = Field(description="The text found (or empty string if missing)")
    differences: str = Field(
        description="What changed — empty if exact match"
    )
    reasoning: str = Field(description="Full judgment")


class VerbatimOutput(BaseModel):
    """Complete structured output from the verbatim explanations judge."""

    sections: list[VerbatimSection] = Field(description="Always 5 entries")
    explanation: str = Field(description="Overall summary")


# --- Lesson Structure Eval Models ---


class SectionPresence(BaseModel):
    """Whether a required section is present in the lesson."""

    expected_name: str = Field(description="e.g., 'Model, Explain & Engage'")
    found: bool = Field(description="Is section present?")
    actual_heading: Optional[str] = Field(
        default=None, description="What the section was actually labeled"
    )
    reasoning: str = Field(description="Noting any naming variations")


class MarkerCheck(BaseModel):
    """Whether a required marker is present and used correctly."""

    marker_name: str = Field(description="e.g., 'Teacher Does'")
    marker_symbol: str = Field(description="e.g., '{...}'")
    is_correct: bool = Field(
        description="Present AND used for intended purpose"
    )
    consistency_note: str = Field(description="Where it's used/missing")
    issues: str = Field(description="What's wrong — empty if correct")
    reasoning: str = Field(description="Full judgment")


class StructureOutput(BaseModel):
    """Complete structured output from the lesson structure judge."""

    sections: list[SectionPresence] = Field(description="Always 8 entries")
    markers: list[MarkerCheck] = Field(description="Always 7 entries")
    explanation: str = Field(description="Overall summary")


# --- Think-Aloud Eval Models ---


class ThinkAloudInstance(BaseModel):
    """Evaluation of a single section where students perform independent work."""

    section: str = Field(description="Which section (e.g., 'Guided Practice', 'Application')")
    task_description: str = Field(description="What students are asked to do independently")
    worked_example_present: bool = Field(
        description="Does the teacher do a full worked example before students try?"
    )
    uses_specific_word: bool = Field(
        description="Does the example use a specific word (e.g., 'zebra'), not a generic placeholder?"
    )
    narrates_reasoning: bool = Field(
        description="Does the teacher narrate internal thinking ('I am thinking...', 'So I know...', 'I hear...')?"
    )
    shows_steps_sequentially: bool = Field(
        description="Does the teacher walk through each step of the process one at a time?"
    )
    connects_sound_to_letter: bool = Field(
        description="Does the teacher explicitly link the sound to its letter ('the /z/ sound is written with letter z')?"
    )
    evidence: str = Field(description="Quoted text from the lesson supporting the judgment")


class ThinkAloudOutput(BaseModel):
    """Complete structured output from the think-aloud judge."""

    instances: list[ThinkAloudInstance] = Field(
        description="One entry per section requiring independent student work (expect 1-2)"
    )
    explanation: str = Field(description="Overall summary")


# --- Corrective Feedback Eval Models ---


class CorrectiveFeedbackBlock(BaseModel):
    """A single corrective feedback block found in the lesson."""

    location: str = Field(description="Which section it appears in")
    anticipated_error: str = Field(
        description="What error is described (e.g., 'children may write s instead of z')"
    )
    is_plausible: bool = Field(
        description="Is this a realistic error for this letter/sound/grade level?"
    )
    has_scripted_response: bool = Field(
        description="Does the teacher correction include actual dialogue (not just 'correct if needed')?"
    )
    explains_difference: bool = Field(
        description="Does the correction explain WHY the student's answer is wrong or how to distinguish correct from incorrect?"
    )
    engages_students: bool = Field(
        description="Does the correction involve students (e.g., 'try both sounds', 'what's different?') rather than just telling them?"
    )
    evidence: str = Field(description="Quoted text from the lesson")


class CorrectiveFeedbackOutput(BaseModel):
    """Complete structured output from the corrective feedback judge."""

    blocks: list[CorrectiveFeedbackBlock] = Field(
        description="All corrective feedback found (empty list if none)"
    )
    explanation: str = Field(description="Overall summary")


# --- Post-Response Explanation Eval Models ---


class StudentResponse(BaseModel):
    """A single student response and what follows it."""

    response_text: str = Field(
        description="What students said/did (e.g., 'children say /z/')"
    )
    followed_by: Literal["explanation", "confirmation_only", "nothing"] = Field(
        description="What the teacher says after"
    )
    teacher_text: str = Field(description="The actual teacher response text")


class ActivityResponses(BaseModel):
    """Student responses within a single activity."""

    section: str = Field(description="Which section")
    activity_name: str = Field(description="Name of the activity")
    first_two_responses: list[StudentResponse] = Field(
        description="The first 1-2 student responses in this activity (max 2)"
    )


class PostResponseOutput(BaseModel):
    """Complete structured output from the post-response explanation judge."""

    activities: list[ActivityResponses] = Field(
        description="All activities with student responses in Sections 1-4"
    )
    explanation: str = Field(description="Overall summary")


# --- Sound/Letter Comparison Eval Models ---


class ComparisonBlock(BaseModel):
    """A comparison between target and confusable sound/letter."""

    location: str = Field(description="Which section")
    target: str = Field(description="Target sound/letter (e.g., '/z/' or 'letter z')")
    compared_with: str = Field(
        description="The confusable partner (e.g., '/s/' or 'letter s')"
    )
    describes_similarity: bool = Field(
        description="Does the lesson describe how the two are similar?"
    )
    describes_difference: bool = Field(
        description="Does the lesson describe how the two differ?"
    )
    includes_articulatory_detail: bool = Field(
        description="Does the comparison include mouth/lip/tongue/voicing descriptions?"
    )
    students_produce_both: bool = Field(
        description="Do students actively try producing or writing both sounds/letters?"
    )
    evidence: str = Field(description="Quoted text from the lesson")


class SoundLetterComparisonOutput(BaseModel):
    """Complete structured output from the sound/letter comparison judge."""

    comparisons: list[ComparisonBlock] = Field(
        description="All comparison blocks found (empty list if none)"
    )
    explanation: str = Field(description="Overall summary")


# --- Script Specificity Eval Models ---


class SectionSpecificity(BaseModel):
    """Specificity analysis for a single lesson section."""

    section: str = Field(description="Which section")
    dialogue_lines: int = Field(
        description="Count of lines with actual quoted/scripted teacher speech"
    )
    stage_directions: int = Field(
        description="Count of summarized descriptions (e.g., '{Teacher reads words...}')"
    )
    specific_example_words: list[str] = Field(
        description="Specific words used as examples in sound activities (e.g., ['zebra', 'tiger'])"
    )
    specific_child_responses: int = Field(
        description="Child responses with actual content (e.g., 'children say /z/')"
    )
    generic_child_responses: int = Field(
        description="Generic child responses (e.g., 'children respond', 'children answer')"
    )
    has_pacing_cues: bool = Field(
        description="Does the section include pacing/management cues (e.g., 'Ready. Go.', 'My turn. Your turn.')?"
    )
    evidence_sample: str = Field(
        description="Representative excerpt showing the section's specificity level"
    )


class ScriptSpecificityOutput(BaseModel):
    """Complete structured output from the script specificity judge."""

    sections: list[SectionSpecificity] = Field(
        description="One entry per section (1-4)"
    )
    explanation: str = Field(description="Overall summary")
