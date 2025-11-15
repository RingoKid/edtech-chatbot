"""
Handwriting Analysis Service using OpenCV.
Analyzes uploaded handwriting images and videos, extracts geometric features.
"""

import cv2
import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import math
import tempfile
import os

logger = logging.getLogger(__name__)


class GeometricFeatures:
    """Container for extracted geometric features from handwriting analysis."""

    def __init__(self):
        self.stroke_count: int = 0
        self.contour_count: int = 0
        self.stroke_continuity: str = "unknown"  # "continuous", "broken", "fragmented"
        self.line_straightness: float = 0.0  # 0-1 score, 1 being perfectly straight
        self.baseline_alignment: str = "unknown"  # "good", "tilted_left", "tilted_right", "inconsistent"
        self.slant_angle: float = 0.0  # degrees
        self.aspect_ratio: float = 0.0  # height/width
        self.symmetry_score: float = 0.0  # 0-1 score
        self.bounding_box: Tuple[int, int, int, int] = (0, 0, 0, 0)  # x, y, w, h
        self.contour_complexity: float = 0.0  # perimeter to area ratio

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "stroke_count": self.stroke_count,
            "contour_count": self.contour_count,
            "stroke_continuity": self.stroke_continuity,
            "line_straightness": round(self.line_straightness, 2),
            "baseline_alignment": self.baseline_alignment,
            "slant_angle": round(self.slant_angle, 2),
            "aspect_ratio": round(self.aspect_ratio, 2),
            "symmetry_score": round(self.symmetry_score, 2),
            "bounding_box": {
                "x": int(self.bounding_box[0]),
                "y": int(self.bounding_box[1]),
                "width": int(self.bounding_box[2]),
                "height": int(self.bounding_box[3])
            },
            "contour_complexity": round(self.contour_complexity, 2)
        }


class ImageProcessor:
    """Handles image preprocessing for handwriting analysis."""

    @staticmethod
    def preprocess_image(image_path: str) -> Tuple[np.ndarray, np.ndarray]:
        """
        Load and preprocess image for analysis.

        Args:
            image_path: Path to the image file

        Returns:
            Tuple of (original_image, preprocessed_binary_image)
        """
        # Read image
        img = cv2.imread(image_path)
        if img is None:
            raise ValueError(f"Failed to load image from {image_path}")

        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

        # Apply Gaussian blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)

        # Apply adaptive thresholding for better edge detection
        binary = cv2.adaptiveThreshold(
            blurred,
            255,
            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY_INV,
            11,
            2
        )

        # Morphological operations to clean up the image
        kernel = np.ones((3, 3), np.uint8)
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel, iterations=1)

        logger.info(f"Preprocessed image: {img.shape} -> {binary.shape}")
        return img, binary

    @staticmethod
    def resize_if_needed(image: np.ndarray, max_dimension: int = 1500) -> np.ndarray:
        """
        Resize image if it's too large, maintaining aspect ratio.

        Args:
            image: Input image
            max_dimension: Maximum width or height

        Returns:
            Resized image
        """
        h, w = image.shape[:2]
        if max(h, w) > max_dimension:
            scale = max_dimension / max(h, w)
            new_w = int(w * scale)
            new_h = int(h * scale)
            return cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
        return image


class FeatureExtractor:
    """Extracts geometric features from preprocessed handwriting images."""

    @staticmethod
    def extract_contours(binary_image: np.ndarray) -> List[np.ndarray]:
        """
        Extract contours from binary image.

        Args:
            binary_image: Preprocessed binary image

        Returns:
            List of contours sorted by area (largest first)
        """
        contours, _ = cv2.findContours(
            binary_image,
            cv2.RETR_EXTERNAL,
            cv2.CHAIN_APPROX_SIMPLE
        )

        # Filter out very small contours (noise)
        min_area = 50
        contours = [cnt for cnt in contours if cv2.contourArea(cnt) > min_area]

        # Sort by area (largest first)
        contours = sorted(contours, key=cv2.contourArea, reverse=True)

        logger.info(f"Found {len(contours)} significant contours")
        return contours

    @staticmethod
    def analyze_stroke_continuity(contours: List[np.ndarray], binary_image: np.ndarray) -> str:
        """
        Analyze whether strokes are continuous or broken.

        Args:
            contours: List of detected contours
            binary_image: Binary image

        Returns:
            "continuous", "broken", or "fragmented"
        """
        if not contours:
            return "unknown"

        # Count number of separate components
        num_components = len(contours)

        # Calculate average gap between components
        if num_components == 1:
            return "continuous"
        elif num_components <= 3:
            return "broken"
        else:
            return "fragmented"

    @staticmethod
    def calculate_line_straightness(contour: np.ndarray) -> float:
        """
        Calculate how straight the contour is.

        Args:
            contour: Single contour

        Returns:
            Straightness score (0-1, where 1 is perfectly straight)
        """
        if len(contour) < 5:
            return 0.0

        # Fit an ellipse to the contour
        try:
            ellipse = cv2.fitEllipse(contour)
            # Get aspect ratio of fitted ellipse
            (ma, MA) = ellipse[1]  # Minor and major axes
            if MA == 0:
                return 0.0

            # More elongated ellipse = straighter line
            straightness = min(ma, MA) / max(ma, MA) if max(ma, MA) > 0 else 0.0
            # Invert: lower ratio = straighter
            return 1.0 - straightness
        except:
            return 0.0

    @staticmethod
    def detect_baseline_alignment(contours: List[np.ndarray], image_shape: Tuple) -> Tuple[str, float]:
        """
        Detect baseline alignment and tilt angle.

        Args:
            contours: List of contours
            image_shape: Shape of the image

        Returns:
            Tuple of (alignment_description, angle_in_degrees)
        """
        if not contours:
            return "unknown", 0.0

        # Get bottom points of all contours
        bottom_points = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            bottom_y = y + h
            bottom_points.append((x + w//2, bottom_y))

        if len(bottom_points) < 2:
            return "unknown", 0.0

        # Fit a line to bottom points
        points_array = np.array(bottom_points, dtype=np.float32)
        [vx, vy, x, y] = cv2.fitLine(points_array, cv2.DIST_L2, 0, 0.01, 0.01)

        # Calculate angle
        angle = math.degrees(math.atan2(vy, vx))

        # Normalize angle to [-45, 45]
        if angle > 45:
            angle -= 90
        elif angle < -45:
            angle += 90

        # Classify alignment
        if abs(angle) < 5:
            alignment = "good"
        elif angle < -5:
            alignment = "tilted_left"
        elif angle > 5:
            alignment = "tilted_right"
        else:
            alignment = "inconsistent"

        return alignment, angle

    @staticmethod
    def calculate_slant_angle(contour: np.ndarray) -> float:
        """
        Calculate the slant angle of handwriting.

        Args:
            contour: Main contour

        Returns:
            Slant angle in degrees (negative = left, positive = right)
        """
        if len(contour) < 5:
            return 0.0

        # Get the minimum area rectangle
        rect = cv2.minAreaRect(contour)
        angle = rect[2]

        # Normalize angle
        if angle < -45:
            angle = 90 + angle

        return angle

    @staticmethod
    def calculate_aspect_ratio(contour: np.ndarray) -> float:
        """
        Calculate height to width ratio.

        Args:
            contour: Contour to analyze

        Returns:
            Aspect ratio (height/width)
        """
        x, y, w, h = cv2.boundingRect(contour)
        if w == 0:
            return 0.0
        return h / w

    @staticmethod
    def extract_all_features(image_path: str) -> GeometricFeatures:
        """
        Extract all geometric features from an image.

        Args:
            image_path: Path to the handwriting image

        Returns:
            GeometricFeatures object with all extracted features
        """
        features = GeometricFeatures()

        try:
            # Preprocess image
            original, binary = ImageProcessor.preprocess_image(image_path)

            # Resize if too large
            binary = ImageProcessor.resize_if_needed(binary)

            # Extract contours
            contours = FeatureExtractor.extract_contours(binary)

            if not contours:
                logger.warning("No contours found in image")
                return features

            # Use the largest contour as the main handwriting
            main_contour = contours[0]

            # Extract features
            features.contour_count = len(contours)
            features.stroke_count = len(contours)  # Approximation
            features.stroke_continuity = FeatureExtractor.analyze_stroke_continuity(
                contours, binary
            )
            features.line_straightness = FeatureExtractor.calculate_line_straightness(
                main_contour
            )

            alignment, angle = FeatureExtractor.detect_baseline_alignment(
                contours, binary.shape
            )
            features.baseline_alignment = alignment
            features.slant_angle = FeatureExtractor.calculate_slant_angle(main_contour)

            features.aspect_ratio = FeatureExtractor.calculate_aspect_ratio(main_contour)
            features.bounding_box = cv2.boundingRect(main_contour)

            # Calculate contour complexity (perimeter to area ratio)
            perimeter = cv2.arcLength(main_contour, True)
            area = cv2.contourArea(main_contour)
            features.contour_complexity = perimeter / area if area > 0 else 0.0

            logger.info(f"Feature extraction completed: {features.stroke_count} strokes detected")
            return features

        except Exception as e:
            logger.error(f"Error extracting features: {e}")
            raise


class HandwritingAnalysisService:
    """
    Main service for handwriting image analysis.
    Coordinates image processing and feature extraction.
    """

    @staticmethod
    async def analyze_image(image_path: str) -> Dict[str, Any]:
        """
        Analyze a handwriting image and extract geometric features.

        Args:
            image_path: Path to the uploaded image

        Returns:
            Dictionary containing analysis results
        """
        try:
            logger.info(f"Starting analysis for image: {image_path}")

            # Extract features
            features = FeatureExtractor.extract_all_features(image_path)

            # Build result
            result = {
                "status": "success",
                "geometric_features": features.to_dict(),
                "analysis_summary": HandwritingAnalysisService._generate_summary(features)
            }

            logger.info("Analysis completed successfully")
            return result

        except Exception as e:
            logger.error(f"Analysis failed: {e}")
            return {
                "status": "error",
                "error_message": str(e),
                "geometric_features": None,
                "analysis_summary": None
            }

    @staticmethod
    def _generate_summary(features: GeometricFeatures) -> str:
        """
        Generate a human-readable summary of the analysis.

        Args:
            features: Extracted geometric features

        Returns:
            Summary string
        """
        summary_parts = []

        # Stroke continuity
        if features.stroke_continuity == "continuous":
            summary_parts.append("Strokes are well-connected")
        elif features.stroke_continuity == "broken":
            summary_parts.append("Some breaks in strokes detected")
        else:
            summary_parts.append("Multiple fragmented strokes")

        # Baseline alignment
        if features.baseline_alignment == "good":
            summary_parts.append("Good baseline alignment")
        else:
            summary_parts.append(f"Baseline is {features.baseline_alignment}")

        # Line straightness
        if features.line_straightness > 0.7:
            summary_parts.append("Very straight lines")
        elif features.line_straightness > 0.4:
            summary_parts.append("Moderately straight lines")
        else:
            summary_parts.append("Curved or irregular lines")

        return ". ".join(summary_parts) + "."


class VideoProcessor:
    """Handles video preprocessing and frame extraction for handwriting analysis."""

    @staticmethod
    def extract_key_frames(video_path: str, num_frames: int = 3) -> List[str]:
        """
        Extract key frames from video at specific intervals.

        Args:
            video_path: Path to the video file
            num_frames: Number of key frames to extract (default: 3)

        Returns:
            List of paths to extracted frame images

        Raises:
            ValueError: If video cannot be opened or has issues
        """
        logger.info(f"Extracting {num_frames} key frames from video: {video_path}")

        # Open video file
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            raise ValueError(f"Failed to open video file: {video_path}")

        try:
            # Get video properties
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            fps = cap.get(cv2.CAP_PROP_FPS)
            duration = total_frames / fps if fps > 0 else 0

            logger.info(f"Video info: {total_frames} frames, {fps:.2f} FPS, {duration:.2f}s duration")

            if total_frames < num_frames:
                logger.warning(f"Video has fewer frames ({total_frames}) than requested ({num_frames})")
                num_frames = max(1, total_frames)

            # Calculate frame positions (10%, 50%, 90% for 3 frames)
            if num_frames == 3:
                frame_positions = [0.10, 0.50, 0.90]
            elif num_frames == 5:
                frame_positions = [0.10, 0.30, 0.50, 0.70, 0.90]
            else:
                # Evenly distribute frames
                frame_positions = [i / (num_frames - 1) for i in range(num_frames)]

            frame_indices = [int(pos * total_frames) for pos in frame_positions]

            # Extract frames
            frame_paths = []
            temp_dir = tempfile.gettempdir()
            video_basename = Path(video_path).stem

            for idx, frame_idx in enumerate(frame_indices):
                # Set video position
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()

                if not ret:
                    logger.warning(f"Failed to read frame at index {frame_idx}")
                    continue

                # Save frame as temporary image
                frame_filename = f"{video_basename}_frame_{idx+1}_at_{frame_positions[idx]*100:.0f}pct.jpg"
                frame_path = os.path.join(temp_dir, frame_filename)

                cv2.imwrite(frame_path, frame)
                frame_paths.append(frame_path)
                logger.info(f"Extracted frame {idx+1}/{num_frames} at {frame_positions[idx]*100:.0f}% -> {frame_path}")

            logger.info(f"Successfully extracted {len(frame_paths)} frames")
            return frame_paths

        finally:
            cap.release()

    @staticmethod
    def save_frames_permanently(frame_paths: List[str], output_dir: Path, job_id: str) -> List[str]:
        """
        Copy extracted frames from temp directory to permanent storage.

        Args:
            frame_paths: List of temporary frame paths
            output_dir: Directory to save frames permanently
            job_id: Job ID for unique filenames

        Returns:
            List of permanent frame paths
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        permanent_paths = []

        for idx, temp_path in enumerate(frame_paths):
            if not os.path.exists(temp_path):
                logger.warning(f"Temp frame not found: {temp_path}")
                continue

            # Create permanent filename
            frame_ext = Path(temp_path).suffix
            permanent_filename = f"{job_id}_frame_{idx+1}{frame_ext}"
            permanent_path = output_dir / permanent_filename

            # Copy file
            import shutil
            shutil.copy2(temp_path, permanent_path)
            permanent_paths.append(str(permanent_path))
            logger.info(f"Saved frame {idx+1} to: {permanent_path}")

        return permanent_paths


class HandwritingVideoAnalysisService:
    """
    Service for handwriting video analysis.
    Extracts key frames and analyzes handwriting progression over time.
    """

    @staticmethod
    async def analyze_video(video_path: str, output_dir: Optional[Path] = None, job_id: str = "video") -> Dict[str, Any]:
        """
        Analyze a handwriting video by extracting key frames and analyzing each.

        Args:
            video_path: Path to the uploaded video
            output_dir: Directory to save extracted frames (optional)
            job_id: Job ID for organizing output files

        Returns:
            Dictionary containing aggregated analysis results
        """
        try:
            logger.info(f"Starting video analysis for: {video_path}")

            # Step 1: Extract key frames (3 frames: beginning, middle, end)
            frame_paths = VideoProcessor.extract_key_frames(video_path, num_frames=3)

            if not frame_paths:
                raise ValueError("No frames could be extracted from video")

            # Step 2: Save frames permanently if output directory provided
            permanent_frame_paths = frame_paths
            if output_dir:
                permanent_frame_paths = VideoProcessor.save_frames_permanently(
                    frame_paths, output_dir, job_id
                )

            # Step 3: Analyze each frame
            frame_analyses = []
            for idx, frame_path in enumerate(frame_paths):
                logger.info(f"Analyzing frame {idx+1}/{len(frame_paths)}")

                # Extract features from frame
                features = FeatureExtractor.extract_all_features(frame_path)
                frame_analyses.append({
                    "frame_number": idx + 1,
                    "frame_path": permanent_frame_paths[idx] if output_dir else frame_path,
                    "features": features.to_dict(),
                    "summary": HandwritingAnalysisService._generate_summary(features)
                })

            # Step 4: Aggregate analysis across frames
            aggregated_features = HandwritingVideoAnalysisService._aggregate_features(frame_analyses)
            progression_analysis = HandwritingVideoAnalysisService._analyze_progression(frame_analyses)

            # Build result
            result = {
                "status": "success",
                "video_path": video_path,
                "total_frames_analyzed": len(frame_analyses),
                "frame_analyses": frame_analyses,
                "aggregated_features": aggregated_features,
                "progression_analysis": progression_analysis,
                "analysis_summary": HandwritingVideoAnalysisService._generate_video_summary(
                    aggregated_features, progression_analysis
                )
            }

            logger.info("Video analysis completed successfully")
            return result

        except Exception as e:
            logger.error(f"Video analysis failed: {e}")
            return {
                "status": "error",
                "error_message": str(e),
                "video_path": video_path,
                "total_frames_analyzed": 0,
                "frame_analyses": [],
                "aggregated_features": None,
                "progression_analysis": None,
                "analysis_summary": None
            }

    @staticmethod
    def _aggregate_features(frame_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Aggregate features across all frames (average values).

        Args:
            frame_analyses: List of frame analysis results

        Returns:
            Dictionary of aggregated features
        """
        if not frame_analyses:
            return {}

        # Collect numeric features
        stroke_counts = []
        line_straightness = []
        slant_angles = []
        aspect_ratios = []

        for analysis in frame_analyses:
            features = analysis["features"]
            stroke_counts.append(features["stroke_count"])
            line_straightness.append(features["line_straightness"])
            slant_angles.append(features["slant_angle"])
            aspect_ratios.append(features["aspect_ratio"])

        # Calculate averages
        return {
            "avg_stroke_count": round(np.mean(stroke_counts), 2),
            "avg_line_straightness": round(np.mean(line_straightness), 2),
            "avg_slant_angle": round(np.mean(slant_angles), 2),
            "avg_aspect_ratio": round(np.mean(aspect_ratios), 2),
            "stroke_count_range": [min(stroke_counts), max(stroke_counts)],
            "most_common_continuity": frame_analyses[0]["features"]["stroke_continuity"],
            "most_common_baseline": frame_analyses[0]["features"]["baseline_alignment"]
        }

    @staticmethod
    def _analyze_progression(frame_analyses: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Analyze how handwriting changes throughout the video.

        Args:
            frame_analyses: List of frame analysis results

        Returns:
            Dictionary describing handwriting progression
        """
        if len(frame_analyses) < 2:
            return {"progression": "insufficient_frames"}

        # Compare first and last frame
        first = frame_analyses[0]["features"]
        last = frame_analyses[-1]["features"]

        # Calculate changes
        stroke_change = last["stroke_count"] - first["stroke_count"]
        straightness_change = last["line_straightness"] - first["line_straightness"]

        # Determine progression type
        if abs(stroke_change) <= 1 and abs(straightness_change) < 0.1:
            progression_type = "consistent"
        elif straightness_change > 0.1:
            progression_type = "improving"
        elif straightness_change < -0.1:
            progression_type = "declining"
        else:
            progression_type = "variable"

        return {
            "progression_type": progression_type,
            "stroke_count_change": stroke_change,
            "straightness_change": round(straightness_change, 2),
            "consistency_score": round(1.0 - abs(straightness_change), 2)
        }

    @staticmethod
    def _generate_video_summary(aggregated_features: Dict[str, Any], progression: Dict[str, Any]) -> str:
        """
        Generate human-readable summary of video analysis.

        Args:
            aggregated_features: Aggregated feature statistics
            progression: Progression analysis results

        Returns:
            Summary string
        """
        if not aggregated_features or not progression:
            return "Unable to generate summary due to analysis errors."

        summary_parts = []

        # Overall consistency
        prog_type = progression.get("progression_type", "unknown")
        if prog_type == "consistent":
            summary_parts.append("Handwriting remains consistent throughout the video")
        elif prog_type == "improving":
            summary_parts.append("Handwriting shows improvement as writing progresses")
        elif prog_type == "declining":
            summary_parts.append("Handwriting quality decreases toward the end (possible fatigue)")
        else:
            summary_parts.append("Handwriting quality varies throughout the video")

        # Average characteristics
        avg_straightness = aggregated_features.get("avg_line_straightness", 0)
        if avg_straightness > 0.7:
            summary_parts.append("Lines are generally straight")
        elif avg_straightness > 0.4:
            summary_parts.append("Lines show moderate straightness")
        else:
            summary_parts.append("Lines tend to be curved")

        return ". ".join(summary_parts) + "."