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
        "letter_formation",
        "fine_motor",
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
    # Add vocabulary-specific fields here later
    pass


class IdeaGenerationParams(BaseLessonParams):
    """Parameters specific to idea generation lessons."""
    # Add idea generation-specific fields here later
    pass
