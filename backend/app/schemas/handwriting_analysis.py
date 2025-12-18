"""
Pydantic schemas for handwriting image analysis endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from enum import Enum


class GradeLevelEnum(str, Enum):
    """Grade levels for handwriting analysis."""
    PREK = "prek"
    KINDERGARTEN = "kindergarten"
    GRADE_1 = "grade_1"
    GRADE_2 = "grade_2"
    GRADE_3 = "grade_3"
    GRADE_4_PLUS = "grade_4_plus"


class AnalysisStatusEnum(str, Enum):
    """Status of handwriting analysis job."""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class BoundingBox(BaseModel):
    """Bounding box coordinates."""
    x: int
    y: int
    width: int
    height: int


class GeometricFeaturesSchema(BaseModel):
    """Geometric features extracted from handwriting image."""
    stroke_count: int = Field(..., description="Number of detected strokes")
    contour_count: int = Field(..., description="Number of detected contours")
    stroke_continuity: str = Field(..., description="Stroke continuity: continuous, broken, or fragmented")
    line_straightness: float = Field(..., ge=0.0, le=1.0, description="Line straightness score (0-1)")
    baseline_alignment: str = Field(..., description="Baseline alignment: good, tilted_left, tilted_right, or inconsistent")
    slant_angle: float = Field(..., description="Slant angle in degrees")
    aspect_ratio: float = Field(..., description="Height to width ratio")
    symmetry_score: float = Field(..., ge=0.0, le=1.0, description="Symmetry score (0-1)")
    bounding_box: BoundingBox = Field(..., description="Bounding box of the handwriting")
    contour_complexity: float = Field(..., description="Perimeter to area ratio")


class ImageAnalysisRequest(BaseModel):
    """Request schema for image analysis (used with form data metadata)."""
    thread_id: Optional[str] = Field(None, description="Optional conversation thread ID")
    grade_level: Optional[GradeLevelEnum] = Field(None, description="Student grade level for context")
    target_letter: Optional[str] = Field(None, description="What letter/word the student intended to write")
    teacher_id: Optional[str] = Field(None, description="Teacher/user ID")


class ImageAnalysisJobResponse(BaseModel):
    """Immediate response after image upload."""
    job_id: str = Field(..., description="Unique job ID for tracking analysis")
    thread_id: str = Field(..., description="Conversation thread ID")
    status: AnalysisStatusEnum = Field(..., description="Current job status")
    message: str = Field(..., description="Status message")


class AnalysisResult(BaseModel):
    """Complete analysis result."""
    job_id: str = Field(..., description="Job ID")
    thread_id: str = Field(..., description="Conversation thread ID")
    status: AnalysisStatusEnum = Field(..., description="Analysis status")
    image_path: Optional[str] = Field(None, description="Path to stored image")
    detected_character: Optional[str] = Field(None, description="Detected character (if applicable)")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Detection confidence")
    geometric_features: Optional[GeometricFeaturesSchema] = Field(None, description="Extracted geometric features")
    feedback: Optional[str] = Field(None, description="LLM-generated feedback")
    suggestions: Optional[List[str]] = Field(None, description="Improvement suggestions")
    grade_level: Optional[GradeLevelEnum] = Field(None, description="Grade level context")
    target_letter: Optional[str] = Field(None, description="Target letter/word")
    analysis_summary: Optional[str] = Field(None, description="Human-readable summary")
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")
    created_at: str = Field(..., description="Timestamp of job creation")
    completed_at: Optional[str] = Field(None, description="Timestamp of job completion")


class AnalysisJobStatusResponse(BaseModel):
    """Response for job status check."""
    job_id: str = Field(..., description="Job ID")
    status: AnalysisStatusEnum = Field(..., description="Current status")
    result: Optional[AnalysisResult] = Field(None, description="Analysis result if completed")


class AnalysisHistoryResponse(BaseModel):
    """Response for user's analysis history."""
    teacher_id: str = Field(..., description="Teacher ID")
    total_analyses: int = Field(..., description="Total number of analyses")
    analyses: List[AnalysisResult] = Field(..., description="List of analysis results")


# ===========================
# VIDEO ANALYSIS SCHEMAS
# ===========================

class FrameAnalysis(BaseModel):
    """Analysis result for a single video frame."""
    frame_number: int = Field(..., description="Frame sequence number")
    frame_path: str = Field(..., description="Path to extracted frame image")
    features: Dict[str, Any] = Field(..., description="Geometric features for this frame")
    summary: str = Field(..., description="Summary of this frame's analysis")


class AggregatedFeatures(BaseModel):
    """Aggregated features across all video frames."""
    avg_stroke_count: float = Field(..., description="Average stroke count across frames")
    avg_line_straightness: float = Field(..., description="Average line straightness (0-1)")
    avg_slant_angle: float = Field(..., description="Average slant angle in degrees")
    avg_aspect_ratio: float = Field(..., description="Average aspect ratio")
    stroke_count_range: List[int] = Field(..., description="[min, max] stroke counts")
    most_common_continuity: str = Field(..., description="Most common stroke continuity type")
    most_common_baseline: str = Field(..., description="Most common baseline alignment")


class ProgressionAnalysis(BaseModel):
    """Analysis of handwriting progression throughout video."""
    progression_type: str = Field(..., description="Type: consistent, improving, declining, variable")
    stroke_count_change: int = Field(..., description="Change from first to last frame")
    straightness_change: float = Field(..., description="Change in line straightness")
    consistency_score: float = Field(..., ge=0.0, le=1.0, description="How consistent the writing is (0-1)")


class VideoAnalysisResult(BaseModel):
    """Complete video analysis result."""
    job_id: str = Field(..., description="Job ID")
    thread_id: str = Field(..., description="Conversation thread ID")
    status: AnalysisStatusEnum = Field(..., description="Analysis status")
    video_path: Optional[str] = Field(None, description="Path to stored video")
    total_frames_analyzed: int = Field(..., description="Number of frames analyzed")
    frame_analyses: List[FrameAnalysis] = Field(..., description="Analysis for each frame")
    aggregated_features: Optional[AggregatedFeatures] = Field(None, description="Aggregated stats")
    progression_analysis: Optional[ProgressionAnalysis] = Field(None, description="Progression analysis")
    feedback: Optional[str] = Field(None, description="LLM-generated feedback")
    suggestions: Optional[List[str]] = Field(None, description="Improvement suggestions")
    grade_level: Optional[str] = Field(None, description="Grade level context")
    target_letter: Optional[str] = Field(None, description="Target letter/word")
    analysis_summary: Optional[str] = Field(None, description="Human-readable summary")
    error_message: Optional[str] = Field(None, description="Error message if analysis failed")
    created_at: str = Field(..., description="Timestamp of job creation")
    completed_at: Optional[str] = Field(None, description="Timestamp of job completion")


class VideoAnalysisJobResponse(BaseModel):
    """Immediate response after video upload."""
    job_id: str = Field(..., description="Unique job ID for tracking analysis")
    thread_id: str = Field(..., description="Conversation thread ID")
    status: AnalysisStatusEnum = Field(..., description="Current job status")
    message: str = Field(..., description="Status message")


class VideoAnalysisJobStatusResponse(BaseModel):
    """Response for video job status check."""
    job_id: str = Field(..., description="Job ID")
    status: AnalysisStatusEnum = Field(..., description="Current status")
    result: Optional[VideoAnalysisResult] = Field(None, description="Video analysis result if completed")