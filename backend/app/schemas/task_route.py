# [New Schema]
from pydantic import BaseModel, Field
from typing import Literal

class TaskRoute(BaseModel):
    """
    Routes the user's request to the correct lesson planning task.
    """
    task_name: Literal["Handwriting", "Vocabulary", "Idea Generation"] = Field(
        ...,
        description="The specific lesson planning task the user wants to start."
    )
