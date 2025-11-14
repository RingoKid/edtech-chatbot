"""
Handwriting Analysis Service using OpenCV.
Analyzes uploaded handwriting images and extracts geometric features.
"""

import cv2
import numpy as np
import logging
from typing import Dict, Any, List, Tuple, Optional
from pathlib import Path
import math

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