"""Pydantic schemas for the image generation pipeline."""

from pydantic import BaseModel, Field, field_validator


class ImageRequest(BaseModel):
    """A single image generation request from the image director agent."""

    prompt: str = Field(
        description="Full image generation prompt (verbose, explicit)"
    )
    placement: str = Field(
        description='Section header to place image after (e.g., "Model, Explain & Engage")'
    )
    alt_text: str = Field(
        description="Accessible description for screen readers"
    )
    pedagogical_role: str = Field(
        description="Why this image exists (for traceability, future eval use)"
    )


class ImagePlan(BaseModel):
    """The image director agent's structured output — exactly 3 images."""

    images: list[ImageRequest] = Field(
        description="Exactly 3 image requests for the lesson"
    )

    @field_validator("images")
    @classmethod
    def exactly_three_images(cls, v: list[ImageRequest]) -> list[ImageRequest]:
        if len(v) != 3:
            raise ValueError(f"ImagePlan must contain exactly 3 images, got {len(v)}")
        return v
