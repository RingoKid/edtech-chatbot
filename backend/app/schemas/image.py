"""Pydantic schemas for the image generation pipeline."""

from pydantic import BaseModel, Field


class ImageRequest(BaseModel):
    """A single image generation request."""

    prompt: str = Field(
        description="Full image generation prompt"
    )
    alt_text: str = Field(
        description="Accessible description for screen readers"
    )
