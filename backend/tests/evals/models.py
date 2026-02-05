"""Pydantic models for structured LLM judge output in scaffolding evals."""

from pydantic import BaseModel, Field
from typing import Literal


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
