"""
Pydantic models for DynamoDB data structures.
"""
from pydantic import BaseModel, Field
from typing import Literal, Dict, Any, List, Optional
from datetime import datetime
from enum import Enum

# Enum definitions
class FormCategoryEnum(str, Enum):
    A = "A"
    B = "B"
    C = "C"
    D = "D"
    E = "E"
    F = "F"
    G = "G"
    H = "H"
    I = "I"
    J = "J"
    K = "K"
    L = "L"
    M = "M"
    N = "N"
    O = "O"
    P = "P"
    Q = "Q"
    PREK_STANDARDS = "prek_standards"
    KINDERGARTEN_STANDARDS = "kindergarten_standards"
    EXAMPLE = "example"

class FormTypeEnum(str, Enum):
    LESSON_STRUCTURE = "lesson_structure"
    ACTIVITY_COLLECTION = "activity_collection"
    REFERENCE_LIST = "reference_list"
    GENRE_GUIDE = "genre_guide"
    STANDARDS = "standards"
    EXAMPLE = "example"

class EducationalDomainEnum(str, Enum):
    HANDWRITING = "handwriting"
    VOCABULARY = "vocabulary"
    IDEAS = "ideas"
    STANDARDS = "standards"
    GENERAL = "general"

class UserRoleEnum(str, Enum):
    TEACHER = "teacher"
    PROFESSOR = "professor"

class JobStatusEnum(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


# Pydantic Models for API
class FormPydantic(BaseModel):
    """Pydantic model for Form API responses."""
    id: str
    category: FormCategoryEnum
    form_type: Optional[FormTypeEnum] = None
    domain: EducationalDomainEnum
    title: str
    description: Optional[str] = None
    content: Dict[str, Any]
    tags: Optional[List[str]] = None
    difficulty_levels: Optional[List[str]] = None
    referenced_forms: Optional[List[str]] = None
    created_by: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class UserPydantic(BaseModel):
    """Pydantic model for User API responses."""
    id: str
    email: str
    role: UserRoleEnum
    full_name: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None

class ChatSessionPydantic(BaseModel):
    """Pydantic model for ChatSession API responses."""
    id: str
    teacher_id: Optional[str] = None
    session_name: Optional[str] = None
    messages: List[Dict[str, Any]]
    last_intent: Optional[str] = None
    last_bot_type: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


# Helper class for form category mapping
class FormCategoryMapping:
    """Maps form categories to educational domains and provides search helpers."""

    @classmethod
    def get_domain_for_category(cls, category: FormCategoryEnum) -> EducationalDomainEnum:
        """Get the educational domain for a form category."""


        if category in handwriting_forms:
            return EducationalDomainEnum.HANDWRITING
        elif category in vocabulary_forms:
            return EducationalDomainEnum.VOCABULARY
        elif category in ideas_forms:
            return EducationalDomainEnum.IDEAS
        elif category in [FormCategoryEnum.PREK_STANDARDS, FormCategoryEnum.KINDERGARTEN_STANDARDS]:
            return EducationalDomainEnum.STANDARDS
        else:
            return EducationalDomainEnum.GENERAL

    @classmethod
    def get_categories_for_domain(cls, domain: EducationalDomainEnum) -> List[FormCategoryEnum]:
        """Get all form categories for an educational domain."""
        if domain == EducationalDomainEnum.HANDWRITING:
            return [FormCategoryEnum.A, FormCategoryEnum.B, FormCategoryEnum.C, FormCategoryEnum.D,
                   FormCategoryEnum.E, FormCategoryEnum.F, FormCategoryEnum.G, FormCategoryEnum.H]
        elif domain == EducationalDomainEnum.VOCABULARY:
            return [FormCategoryEnum.I, FormCategoryEnum.J, FormCategoryEnum.K, FormCategoryEnum.L]
        elif domain == EducationalDomainEnum.IDEAS:
            return [FormCategoryEnum.M, FormCategoryEnum.N, FormCategoryEnum.O, FormCategoryEnum.P, FormCategoryEnum.Q]
        elif domain == EducationalDomainEnum.STANDARDS:
            return [FormCategoryEnum.PREK_STANDARDS, FormCategoryEnum.KINDERGARTEN_STANDARDS]
        else:
            return list(FormCategoryEnum)