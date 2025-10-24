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
    # Add handwriting-specific fields here later
    pass


class VocabularyParams(BaseLessonParams):
    """Parameters specific to vocabulary lessons."""
    # Add vocabulary-specific fields here later
    pass


class IdeaGenerationParams(BaseLessonParams):
    """Parameters specific to idea generation lessons."""
    # Add idea generation-specific fields here later
    pass
