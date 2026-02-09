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
