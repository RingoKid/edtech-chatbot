# [Modify Schema]
from pydantic import BaseModel, Field
from typing import Literal

class TaskRoute(BaseModel):
    """
    Routes the user's request to the correct lesson planning task or indicates clarification is needed.
    """
    task_name: Literal["Handwriting", "Vocabulary", "Idea Generation", "__CLARIFY__"] = Field(
        ...,
        description="The specific lesson planning task the user wants to start, or '__CLARIFY__' if the user's intent is unclear."
    )
