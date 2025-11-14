"""
Handwriting Image Analysis Router.
Handles image upload, processing, and feedback generation.
"""

import asyncio
import os
import uuid
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks
from fastapi.responses import JSONResponse

from app.schemas.handwriting_analysis import (
    ImageAnalysisJobResponse,
    AnalysisJobStatusResponse,
    AnalysisResult,
    AnalysisStatusEnum,
    GradeLevelEnum,
    GeometricFeaturesSchema,
    BoundingBox
)
from app.services.handwriting_analysis_service import HandwritingAnalysisService
from app.services.chat_service import ChatService

# Set up logging
logger = logging.getLogger(__name__)

router = APIRouter(prefix="/handwriting", tags=["Handwriting Analysis"])

# In-memory job storage (will be replaced with DynamoDB later)
analysis_jobs: dict = {}


# Configuration
UPLOAD_DIR = Path(__file__).parent.parent.parent / "uploads" / "handwriting_images"
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".heic", ".heif"}


def ensure_upload_directory():
    """Create upload directory if it doesn't exist."""
    UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
    logger.info(f"Upload directory ready: {UPLOAD_DIR}")


def validate_image_file(file: UploadFile) -> None:
    """
    Validate uploaded image file.

    Args:
        file: Uploaded file

    Raises:
        HTTPException: If file is invalid
    """
    # Check file extension
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"
        )

    # Check file size (if available in headers)
    # Note: file.size is not always available, so we'll check during read


async def save_uploaded_image(
    file: UploadFile,
    thread_id: str,
    job_id: str
) -> str:
    """
    Save uploaded image to disk.

    Args:
        file: Uploaded file
        thread_id: Thread ID for organizing files
        job_id: Job ID for unique filename

    Returns:
        Path to saved file

    Raises:
        HTTPException: If save fails or file too large
    """
    # Create thread-specific directory
    thread_dir = UPLOAD_DIR / thread_id
    thread_dir.mkdir(parents=True, exist_ok=True)

    # Generate filename
    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    file_ext = Path(file.filename).suffix.lower()
    filename = f"{timestamp}_{job_id}{file_ext}"
    file_path = thread_dir / filename

    # Read and save file
    try:
        content = await file.read()

        # Check file size
        if len(content) > MAX_FILE_SIZE:
            raise HTTPException(
                status_code=413,
                detail=f"File too large. Maximum size: {MAX_FILE_SIZE / (1024*1024):.1f}MB"
            )

        # Save to disk
        with open(file_path, "wb") as f:
            f.write(content)

        logger.info(f"Image saved: {file_path}")
        return str(file_path)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error saving image: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save image: {str(e)}")


async def process_handwriting_analysis(
    job_id: str,
    image_path: str,
    thread_id: str,
    grade_level: Optional[str],
    target_letter: Optional[str],
    teacher_id: str,
    user_message: Optional[str] = None
):
    """
    Background task to process handwriting analysis.

    Args:
        job_id: Job ID
        image_path: Path to uploaded image
        thread_id: Conversation thread ID
        grade_level: Student grade level
        target_letter: Target letter/word
        teacher_id: Teacher ID
    """
    try:
        logger.info(f"Starting background analysis for job {job_id}")

        # Update job status
        analysis_jobs[job_id]["status"] = AnalysisStatusEnum.PROCESSING

        # Step 1: Extract geometric features using OpenCV
        analysis_result = await HandwritingAnalysisService.analyze_image(image_path)

        if analysis_result["status"] != "success":
            # Analysis failed
            analysis_jobs[job_id]["status"] = AnalysisStatusEnum.FAILED
            analysis_jobs[job_id]["error_message"] = analysis_result.get(
                "error_message", "Unknown error"
            )
            analysis_jobs[job_id]["completed_at"] = datetime.utcnow().isoformat() + "Z"
            logger.error(f"Analysis failed for job {job_id}")
            return

        # Step 2: Prepare features for LLM feedback
        geometric_features = analysis_result["geometric_features"]
        analysis_summary = analysis_result["analysis_summary"]

        # Convert geometric features to schema
        features_schema = GeometricFeaturesSchema(
            stroke_count=geometric_features["stroke_count"],
            contour_count=geometric_features["contour_count"],
            stroke_continuity=geometric_features["stroke_continuity"],
            line_straightness=geometric_features["line_straightness"],
            baseline_alignment=geometric_features["baseline_alignment"],
            slant_angle=geometric_features["slant_angle"],
            aspect_ratio=geometric_features["aspect_ratio"],
            symmetry_score=geometric_features["symmetry_score"],
            bounding_box=BoundingBox(**geometric_features["bounding_box"]),
            contour_complexity=geometric_features["contour_complexity"]
        )

        # Step 3: Generate LLM feedback using general bot directly
        from app.chatbot.specialists.general.bot import GeneralBot
        from langchain_core.messages import HumanMessage

        # Construct prompt for LLM with geometric features
        grade_context = f" for a {grade_level} student" if grade_level else ""
        target_context = f" The student intended to write: '{target_letter}'." if target_letter else ""

        # Include user message if provided
        user_context = ""
        if user_message:
            user_context = f"\n\nUser's question/comment: \"{user_message}\""

        prompt = f"""Analyze this handwriting sample{grade_context}.{target_context}{user_context}

Geometric Analysis Results:
- Stroke Count: {geometric_features['stroke_count']}
- Stroke Continuity: {geometric_features['stroke_continuity']}
- Line Straightness: {geometric_features['line_straightness']:.2f} (0=curved, 1=straight)
- Baseline Alignment: {geometric_features['baseline_alignment']}
- Slant Angle: {geometric_features['slant_angle']:.1f}°
- Aspect Ratio: {geometric_features['aspect_ratio']:.2f}

Summary: {analysis_summary}

Please provide:
1. Encouraging feedback on what the student did well
2. Specific, constructive suggestions for improvement (with visual guidance where applicable)
3. Keep the tone appropriate for the grade level
4. If the user asked a specific question, make sure to address it directly"""

        # Get LLM feedback from general bot directly (bypassing routing)
        general_bot = GeneralBot()
        feedback_result = await general_bot.process_message(
            message=prompt,
            conversation_history=[],
            intent=None
        )

        llm_feedback = feedback_result.response

        # Step 4: Parse suggestions from LLM response (simple split for now)
        suggestions = [
            line.strip("- •").strip()
            for line in llm_feedback.split("\n")
            if line.strip().startswith(("-", "•", "1.", "2.", "3."))
        ][:5]  # Limit to 5 suggestions

        # Step 5: Update job with complete results
        analysis_jobs[job_id].update({
            "status": AnalysisStatusEnum.COMPLETED,
            "geometric_features": features_schema,
            "feedback": llm_feedback,
            "suggestions": suggestions if suggestions else ["Keep practicing!"],
            "analysis_summary": analysis_summary,
            "completed_at": datetime.utcnow().isoformat() + "Z"
        })

        logger.info(f"Analysis completed successfully for job {job_id}")

    except Exception as e:
        logger.error(f"Error in background analysis for job {job_id}: {e}")
        analysis_jobs[job_id]["status"] = AnalysisStatusEnum.FAILED
        analysis_jobs[job_id]["error_message"] = str(e)
        analysis_jobs[job_id]["completed_at"] = datetime.utcnow().isoformat() + "Z"


@router.post("/analyze-image", response_model=ImageAnalysisJobResponse)
async def analyze_handwriting_image(
    background_tasks: BackgroundTasks,
    image: UploadFile = File(..., description="Handwriting image file"),
    message: Optional[str] = Form(None, description="User's message/question about the handwriting"),
    thread_id: Optional[str] = Form(None, description="Optional conversation thread ID"),
    grade_level: Optional[str] = Form(None, description="Student grade level"),
    target_letter: Optional[str] = Form(None, description="Target letter/word"),
    teacher_id: Optional[str] = Form("default_teacher", description="Teacher ID")
):
    """
    Upload a handwriting image for analysis.

    This endpoint:
    1. Accepts image upload (PNG, JPG, HEIC)
    2. Returns immediately with a job ID
    3. Processes analysis in background (OpenCV + LLM feedback)
    4. Analysis result posted to conversation thread

    **Usage:**
    ```bash
    curl -X POST "http://localhost:8000/api/v1/handwriting/analyze-image" \\
      -F "image=@handwriting.jpg" \\
      -F "grade_level=kindergarten" \\
      -F "target_letter=A"
    ```

    Returns:
        Job ID and status for tracking analysis progress
    """
    try:
        # Ensure upload directory exists
        ensure_upload_directory()

        # Validate file
        validate_image_file(image)

        # Generate job ID and thread ID
        job_id = f"job_{uuid.uuid4().hex[:12]}"

        # Create or use existing thread ID
        if not thread_id:
            chat_service = ChatService()
            thread_id = chat_service.create_new_thread(teacher_id)

        # Save uploaded image
        image_path = await save_uploaded_image(image, thread_id, job_id)

        # Initialize job record
        analysis_jobs[job_id] = {
            "job_id": job_id,
            "thread_id": thread_id,
            "status": AnalysisStatusEnum.PENDING,
            "image_path": image_path,
            "grade_level": grade_level,
            "target_letter": target_letter,
            "teacher_id": teacher_id,
            "created_at": datetime.utcnow().isoformat() + "Z",
            "completed_at": None,
            "geometric_features": None,
            "feedback": None,
            "suggestions": None,
            "error_message": None
        }

        # Start background processing
        background_tasks.add_task(
            process_handwriting_analysis,
            job_id=job_id,
            image_path=image_path,
            thread_id=thread_id,
            grade_level=grade_level,
            target_letter=target_letter,
            teacher_id=teacher_id,
            user_message=message
        )

        logger.info(f"Analysis job created: {job_id}")

        return ImageAnalysisJobResponse(
            job_id=job_id,
            thread_id=thread_id,
            status=AnalysisStatusEnum.PENDING,
            message="Image uploaded successfully. Analysis in progress."
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error creating analysis job: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process image: {str(e)}")


@router.get("/analysis/{job_id}", response_model=AnalysisJobStatusResponse)
async def get_analysis_status(job_id: str):
    """
    Check the status of a handwriting analysis job.

    **Usage:**
    ```bash
    curl "http://localhost:8000/api/v1/handwriting/analysis/job_abc123"
    ```

    Args:
        job_id: The job ID returned from analyze-image endpoint

    Returns:
        Current job status and result (if completed)

    Raises:
        404: Job not found
    """
    if job_id not in analysis_jobs:
        raise HTTPException(status_code=404, detail=f"Job {job_id} not found")

    job_data = analysis_jobs[job_id]
    status = job_data["status"]

    # Build result object if completed
    result = None
    if status == AnalysisStatusEnum.COMPLETED:
        result = AnalysisResult(
            job_id=job_id,
            thread_id=job_data["thread_id"],
            status=status,
            image_path=job_data["image_path"],
            detected_character=job_data.get("target_letter"),
            confidence=None,  # Not implemented yet
            geometric_features=job_data["geometric_features"],
            feedback=job_data["feedback"],
            suggestions=job_data["suggestions"],
            grade_level=job_data.get("grade_level"),
            target_letter=job_data.get("target_letter"),
            analysis_summary=job_data.get("analysis_summary"),
            error_message=None,
            created_at=job_data["created_at"],
            completed_at=job_data["completed_at"]
        )
    elif status == AnalysisStatusEnum.FAILED:
        result = AnalysisResult(
            job_id=job_id,
            thread_id=job_data["thread_id"],
            status=status,
            image_path=job_data["image_path"],
            detected_character=None,
            confidence=None,
            geometric_features=None,
            feedback=None,
            suggestions=None,
            grade_level=job_data.get("grade_level"),
            target_letter=job_data.get("target_letter"),
            analysis_summary=None,
            error_message=job_data.get("error_message"),
            created_at=job_data["created_at"],
            completed_at=job_data["completed_at"]
        )

    return AnalysisJobStatusResponse(
        job_id=job_id,
        status=status,
        result=result
    )


@router.get("/health")
async def health_check():
    """Health check endpoint for handwriting analysis service."""
    return JSONResponse(content={
        "status": "healthy",
        "service": "handwriting_analysis",
        "upload_dir": str(UPLOAD_DIR),
        "max_file_size_mb": MAX_FILE_SIZE / (1024 * 1024),
        "allowed_extensions": list(ALLOWED_EXTENSIONS)
    })