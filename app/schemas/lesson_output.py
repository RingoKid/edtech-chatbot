from __future__ import annotations

from enum import Enum
from typing import Optional

from pydantic import BaseModel


class TaskName(str, Enum):
    HANDWRITING = "Handwriting"
    VOCABULARY = "Vocabulary"
    IDEA_GENERATION = "Idea Generation"


class HandwritingQueryType(str, Enum):
    LETTER_FORMATION = "letter formation"
    FINE_MOTOR = "fine motor"
    SPELLING = "spelling"
    ASSESSMENT = "assessment"
    GENERAL = "general"


class VocabularyQueryType(str, Enum):
    SENTENCE_STRUCTURE = "sentence structure"
    GENERAL = "general"


class IdeaQueryType(str, Enum):
    BRAINSTORMING = "brainstorming"
    GENERAL = "general"


class HandwritingLesson(BaseModel):
    lesson_title: str
    standards: str
    objectives: str
    materials: str
    review_connect: Optional[str] = None
    model_explain_engage: Optional[str] = None
    guided_practice: Optional[str] = None
    application: Optional[str] = None
    wrap_up: Optional[str] = None
    target_grade: str
    query_type: str
    target_letters: Optional[str] = None


class VocabularyLesson(BaseModel):
    lesson_title: str
    standards: str
    objectives: str
    materials: str
    review_connect: str
    model_explain_engage: str
    guided_practice: str
    application: str
    target_grade: str
    query_type: str
    target_vocabulary: Optional[str] = None
    target_genre: Optional[str] = None


class IdeaGenerationLesson(BaseModel):
    lesson_title: str
    standards: str
    objectives: str
    materials: str
    review_connect: str
    model_explain_engage: str
    guided_practice: str
    application: str
    target_grade: str
    query_type: str
    target_genre: str
    target_topic: str


LESSON_SCHEMA_REGISTRY = {
    TaskName.HANDWRITING.value: HandwritingLesson,
    TaskName.VOCABULARY.value: VocabularyLesson,
    TaskName.IDEA_GENERATION.value: IdeaGenerationLesson,
}


