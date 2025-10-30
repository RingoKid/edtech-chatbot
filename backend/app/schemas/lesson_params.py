from pydantic import BaseModel, Field
from typing import Literal


class BaseLessonParams(BaseModel):
    """Base parameters common to most lesson plans."""
    target_grade: Literal["Pre-K", "Kindergarten", "First Grade", "__CLARIFY__"] = Field(
        ...,
        description="What is the target grade level for this lesson?"
    )


class HandwritingParams(BaseLessonParams):
    """Parameters specific to handwriting lessons."""
    query_type: Literal[
        "letter formation",
        "fine motor",
        "spelling",
        "assessment",
        "general",
        "__CLARIFY__"
    ] = Field(
        ...,
        description="Which specific aspect of handwriting do you want to focus on for this lesson?"
    )
    target_letters: str = Field(
        ...,
        description="Which specific letter(s) do you want to focus on for this lesson? (e.g., 'a', 'b, c', or 'None')"
    )


class VocabularyParams(BaseLessonParams):
    """Parameters specific to vocabulary lessons."""
    query_type: Literal[
        "sentence structure",
        "vocabulary building",
        "grammar",
        "genre writing",
        "general",
        "__CLARIFY__"
    ] = Field(
        ...,
        description="Which specific aspect of vocabulary or syntax do you want to focus on?"
    )
    target_vocabulary: str = Field(
        ...,
        description="Are there specific vocabulary words or concepts you want to target? (e.g., 'colors', 'action verbs', 'rhyming words', or 'None')"
    )
    target_genre: str = Field(
        ...,
        description="If focusing on genre writing, which genre? (e.g., 'narrative', 'informational', or 'Not applicable')"
    )


class IdeaGenerationParams(BaseLessonParams):
    """Parameters specific to idea generation lessons."""
    query_type: Literal[
        "idea generation",
        "organization",
        "genre elements",
        "brainstorming",
        "general",
        "__CLARIFY__"
    ] = Field(
        ...,
        description="Which specific aspect of idea generation or organization do you want to focus on?"
    )
    target_genre: Literal[
        "narrative",
        "informational",
        "opinion",
        "personal narrative",
        "compare contrast",
        "__CLARIFY__"
    ] = Field(
        ...,
        description="Which writing genre are we planning for?"
    )
    target_topic: str = Field(
        ...,
        description="What is the specific topic for this writing lesson? (e.g., 'My Family', 'Community Helpers', 'Seasons', or 'Student Choice')"
    )


# Schema registry for looking up classes by name
SCHEMA_REGISTRY = {
    "HandwritingParams": HandwritingParams,
    "VocabularyParams": VocabularyParams,
    "IdeaGenerationParams": IdeaGenerationParams
}
