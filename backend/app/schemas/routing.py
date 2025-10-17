# backend/app/schemas/routing.py

from enum import Enum
from pydantic import BaseModel, Field

class Task(str, Enum):
    """The available lesson-planning tasks."""
    HANDWRITING = "handwriting"
    VOCABULARY = "vocabulary"
    IDEA_GENERATION = "idea_generation"
    GENERAL = "general"

class Route(BaseModel):
    """Select the next task to move to in the conversation."""
    task: Task = Field(
        ...,
        description="The task or topic the user wants to work on."
    )

