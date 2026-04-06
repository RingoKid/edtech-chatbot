"""Graph state for v2 architecture - simplified for agent-based routing."""

from typing import TypedDict, Annotated, List, Optional, Literal
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


# Task type literals for routing
TaskType = Literal["handwriting", "vocabulary", "idea_generation"]

# Grade level literals for handwriting lessons
GradeLevel = Literal["PreK", "K", "1st"]

# Student level literals for differentiation
StudentLevel = Literal["struggling", "on-level", "advanced"]

# Skill focus for activity selection
SkillFocus = Literal["isolating_sounds", "blending", "letter_formation", "spelling"]


class HandwritingParams(TypedDict):
    """
    Parameters for handwriting lesson generation.

    Collected by the param agent before handing off to the generator.
    """
    grade: GradeLevel
    letter: str
    student_level: StudentLevel
    previously_learned: list[str]
    skill_focus: SkillFocus


class ActivityPlan(TypedDict):
    """
    Structured output from the activity planner.

    Each field holds a slug (id) from the activity index.
    Directive fields carry pre-determined pedagogical decisions.
    """
    review: str
    sound_target: str
    handwriting: str
    handwriting_chain: Optional[str]
    spelling: str
    standards: list[str]
    # Lesson directives (Phase 2)
    spelling_pattern: str              # single_sound, VC, CVC, CVCe, CCVC, CVCC
    include_directionality: bool       # whether to teach left-to-right / line placement
    include_articulation: bool         # whether to include mouth/lip/tongue instruction
    guided_practice_techniques: list[str]  # ordered techniques for Section 3
    scaffolding_intensity: str         # heavy, moderate, or light
    content_scope: str                 # 2-3 sentence pedagogical focus description


# Writing type literals for vocabulary lessons
WritingType = Literal["informational", "narrative", "personal_narrative", "opinion"]

# Genre literals for idea generation lessons
Genre = Literal["narrative", "informational", "opinion"]

# Writing stage literals for idea generation lessons
WritingStage = Literal["brainstorm", "initial_draft", "revise", "edit"]


class VocabularySyntaxParams(TypedDict):
    """
    Parameters for vocabulary & sentence structure lesson generation.

    Collected by the param agent before handing off to the generator.
    """
    grade: GradeLevel
    writing_type: WritingType
    key_vocabulary: list[str]
    objectives: str
    student_level: StudentLevel


class IdeaGenerationParams(TypedDict):
    """
    Parameters for idea generation & organization lesson generation.

    Collected by the param agent before handing off to the generator.
    """
    grade: GradeLevel
    genre: Genre
    genre_component: str
    writing_stage: WritingStage
    objectives: str
    student_level: StudentLevel


class FeedbackData(TypedDict):
    """Structured feedback extracted by the feedback collector agent."""
    category: str         # "lesson" | "platform" | "general"
    rating: Optional[int] # 1-5 or None (0 means no rating)
    text: str             # Free-text feedback


class GraphState(TypedDict):
    """
    Unified state object for the routing agent graph.

    v2 Architecture Notes:
    - messages: Full conversation history, managed by add_messages reducer
    - task_type: Set when routing tool is called, indicates destination
    - routing_complete: Signals successful handoff to task agent
    - handwriting_params: Set when param agent collects all handwriting params
    - lesson_finalized: Set when generator's finalize_lesson tool is called
    - feedback_submitted: Set after feedback is collected or skipped
    - feedback_data: Structured feedback for ChatService to persist
    """
    # Messages are handled with add_messages reducer (appends, not replaces)
    messages: Annotated[List[BaseMessage], add_messages]

    # Set by routing tools when user intent is clear
    task_type: Optional[TaskType]

    # Signals that routing has completed and handoff should occur
    routing_complete: bool

    # Handwriting lesson parameters (set by param agent)
    handwriting_params: Optional[HandwritingParams]

    # Activity plan (set by activity planner, used by handwriting generator)
    activity_plan: Optional[ActivityPlan]

    # Vocabulary & syntax lesson parameters (set by param agent)
    vocabulary_params: Optional[VocabularySyntaxParams]

    # Idea generation lesson parameters (set by param agent)
    idea_generation_params: Optional[IdeaGenerationParams]

    # Signals that the lesson has been finalized by the generator
    lesson_finalized: bool

    # Signals that feedback has been submitted or skipped
    feedback_submitted: bool

    # Structured feedback data extracted by the feedback collector
    # Persisted to DynamoDB by ChatService after graph invocation
    feedback_data: Optional[FeedbackData]

    # Latest lesson plan content (overwritten on each generation/modification)
    lesson_markdown: Optional[str]

    # Image generation pipeline (post-lesson generation)
    image_requests: Optional[list[dict]]  # {prompt, alt_text} dicts from image director
    image_urls: Optional[list[str]]  # Pre-computed S3 URLs for the 3 lesson images
