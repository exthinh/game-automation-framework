"""
Screen Analysis - Real Computer Vision Implementation

Complete working implementation with:
- Template matching (OpenCV)
- OCR text recognition (Tesseract)
- Multi-scale matching
- UI element detection
- Confidence scoring

NO PLACEHOLDERS - production-ready code!
"""

import cv2
import numpy as np
import pytesseract
from typing import Optional, Tuple, List, Dict, Any
from pathlib import Path
import logging
from dataclasses import dataclass


@dataclass
class MatchResult:
    """Result from template matching"""
    found: bool
    confidence: float
    location: Optional[Tuple[int, int]] = None  # (x, y) center
    bbox: Optional[Tuple[int, int, int, int]] = None  # (x, y, w, h)

    def __repr__(self) -> str:
        if self.found:
            return f"MatchResult(confidence={self.confidence:.2f}, location={self.location})"
        return f"MatchResult(not found, confidence={self.confidence:.2f})"


class ScreenAnalyzer:
    """
    Complete screen analysis system.

    Provides computer vision capabilities for game automation.
    """

    def __init__(self, templates_dir: str = "templates"):
        """
        Initialize screen analyzer.

        Args:
            templates_dir: Directory containing template images
        """
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(exist_ok=True, parents=True)

        self.logger = logging.getLogger("ScreenAnalyzer")

        # Template cache for performance
        self._template_cache: Dict[str, np.ndarray] = {}

        # OCR configuration
        self.tesseract_config = r'--oem 3 --psm 6'  # Best for game text

        # Detection thresholds
        self.default_confidence_threshold = 0.8
        self.multi_scale_steps = [0.8, 0.9, 1.0, 1.1, 1.2]  # Scale variations

        self.logger.info("Screen Analyzer initialized")

    # ========================================================================
    # TEMPLATE MATCHING
    # ========================================================================

    def find_template(
        self,
        screenshot: np.ndarray,
        template_path: str,
        confidence_threshold: float = None,
        multi_scale: bool = True
    ) -> MatchResult:
        """
        Find template image in screenshot.

        REAL OPENCV IMPLEMENTATION!

        Args:
            screenshot: Screenshot as numpy array (BGR)
            template_path: Path to template image
            confidence_threshold: Minimum confidence (0.0-1.0)
            multi_scale: Try multiple scales

        Returns:
            MatchResult with location if found
        """
        if confidence_threshold is None:
            confidence_threshold = self.default_confidence_threshold

        try:
            # Load template (with caching)
            template = self._load_template(template_path)
            if template is None:
                self.logger.error(f"Failed to load template: {template_path}")
                return MatchResult(found=False, confidence=0.0)

            # Convert to grayscale for better matching
            screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

            if multi_scale:
                return self._find_template_multi_scale(
                    screenshot_gray,
                    template_gray,
                    confidence_threshold
                )
            else:
                return self._find_template_single_scale(
                    screenshot_gray,
                    template_gray,
                    confidence_threshold
                )

        except Exception as e:
            self.logger.error(f"Error in template matching: {e}")
            return MatchResult(found=False, confidence=0.0)

    def _find_template_single_scale(
        self,
        screenshot: np.ndarray,
        template: np.ndarray,
        confidence_threshold: float
    ) -> MatchResult:
        """
        Find template at single scale using OpenCV matchTemplate.

        This is the core OpenCV matching algorithm.
        """
        try:
            # Perform template matching
            result = cv2.matchTemplate(screenshot, template, cv2.TM_CCOEFF_NORMED)

            # Find best match
            min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)

            # max_val is confidence (0.0 to 1.0)
            confidence = float(max_val)

            if confidence >= confidence_threshold:
                # Get template dimensions
                h, w = template.shape[:2]

                # Calculate center point
                top_left_x, top_left_y = max_loc
                center_x = top_left_x + w // 2
                center_y = top_left_y + h // 2

                return MatchResult(
                    found=True,
                    confidence=confidence,
                    location=(center_x, center_y),
                    bbox=(top_left_x, top_left_y, w, h)
                )
            else:
                return MatchResult(found=False, confidence=confidence)

        except Exception as e:
            self.logger.error(f"Error in single-scale matching: {e}")
            return MatchResult(found=False, confidence=0.0)

    def _find_template_multi_scale(
        self,
        screenshot: np.ndarray,
        template: np.ndarray,
        confidence_threshold: float
    ) -> MatchResult:
        """
        Find template at multiple scales (handles size variations).

        Games often have UI elements at slightly different sizes.
        """
        best_result = MatchResult(found=False, confidence=0.0)

        for scale in self.multi_scale_steps:
            # Resize template
            h, w = template.shape[:2]
            new_w = int(w * scale)
            new_h = int(h * scale)

            if new_w <= 0 or new_h <= 0 or new_w > screenshot.shape[1] or new_h > screenshot.shape[0]:
                continue

            scaled_template = cv2.resize(template, (new_w, new_h))

            # Try matching at this scale
            result = self._find_template_single_scale(
                screenshot,
                scaled_template,
                confidence_threshold
            )

            # Keep best result
            if result.confidence > best_result.confidence:
                best_result = result

            # If we found a high-confidence match, we can stop
            if best_result.confidence > 0.95:
                break

        return best_result

    def find_all_templates(
        self,
        screenshot: np.ndarray,
        template_path: str,
        confidence_threshold: float = None
    ) -> List[MatchResult]:
        """
        Find ALL instances of a template in screenshot.

        Useful for finding multiple buttons, resources, etc.

        Args:
            screenshot: Screenshot as numpy array
            template_path: Path to template image
            confidence_threshold: Minimum confidence

        Returns:
            List of MatchResult objects
        """
        if confidence_threshold is None:
            confidence_threshold = self.default_confidence_threshold

        try:
            template = self._load_template(template_path)
            if template is None:
                return []

            screenshot_gray = cv2.cvtColor(screenshot, cv2.COLOR_BGR2GRAY)
            template_gray = cv2.cvtColor(template, cv2.COLOR_BGR2GRAY)

            # Match template
            result = cv2.matchTemplate(screenshot_gray, template_gray, cv2.TM_CCOEFF_NORMED)

            # Find all matches above threshold
            locations = np.where(result >= confidence_threshold)

            matches = []
            h, w = template_gray.shape[:2]

            # Group nearby matches (non-maximum suppression)
            for pt in zip(*locations[::-1]):
                center_x = pt[0] + w // 2
                center_y = pt[1] + h // 2
                confidence = result[pt[1], pt[0]]

                matches.append(MatchResult(
                    found=True,
                    confidence=float(confidence),
                    location=(center_x, center_y),
                    bbox=(pt[0], pt[1], w, h)
                ))

            # Filter overlapping matches
            matches = self._filter_overlapping_matches(matches)

            self.logger.debug(f"Found {len(matches)} instances of template")
            return matches

        except Exception as e:
            self.logger.error(f"Error finding all templates: {e}")
            return []

    def _filter_overlapping_matches(
        self,
        matches: List[MatchResult],
        overlap_threshold: float = 0.5
    ) -> List[MatchResult]:
        """
        Filter overlapping matches using non-maximum suppression.

        Keeps only the best match when multiple matches overlap.
        """
        if not matches:
            return []

        # Sort by confidence (highest first)
        matches = sorted(matches, key=lambda m: m.confidence, reverse=True)

        filtered = []

        for match in matches:
            # Check if this match overlaps with any kept match
            overlap = False

            for kept_match in filtered:
                if self._matches_overlap(match, kept_match, overlap_threshold):
                    overlap = True
                    break

            if not overlap:
                filtered.append(match)

        return filtered

    def _matches_overlap(
        self,
        match1: MatchResult,
        match2: MatchResult,
        threshold: float
    ) -> bool:
        """Check if two matches overlap significantly"""
        if not (match1.bbox and match2.bbox):
            return False

        x1, y1, w1, h1 = match1.bbox
        x2, y2, w2, h2 = match2.bbox

        # Calculate intersection
        x_left = max(x1, x2)
        y_top = max(y1, y2)
        x_right = min(x1 + w1, x2 + w2)
        y_bottom = min(y1 + h1, y2 + h2)

        if x_right < x_left or y_bottom < y_top:
            return False  # No overlap

        intersection_area = (x_right - x_left) * (y_bottom - y_top)
        area1 = w1 * h1
        area2 = w2 * h2

        overlap_ratio = intersection_area / min(area1, area2)

        return overlap_ratio > threshold

    # ========================================================================
    # OCR (TEXT RECOGNITION)
    # ========================================================================

    def read_text(
        self,
        screenshot: np.ndarray,
        region: Optional[Tuple[int, int, int, int]] = None,
        preprocess: bool = True
    ) -> str:
        """
        Read text from screenshot using Tesseract OCR.

        REAL TESSERACT OCR IMPLEMENTATION!

        Args:
            screenshot: Screenshot as numpy array
            region: Optional (x, y, width, height) region to read from
            preprocess: Apply preprocessing for better OCR

        Returns:
            Recognized text
        """
        try:
            # Extract region if specified
            if region:
                x, y, w, h = region
                image = screenshot[y:y+h, x:x+w]
            else:
                image = screenshot

            # Preprocess for better OCR
            if preprocess:
                image = self._preprocess_for_ocr(image)

            # Run Tesseract OCR
            text = pytesseract.image_to_string(image, config=self.tesseract_config)

            # Clean up text
            text = text.strip()

            self.logger.debug(f"OCR result: '{text}'")
            return text

        except Exception as e:
            self.logger.error(f"OCR error: {e}")
            return ""

    def read_numbers(
        self,
        screenshot: np.ndarray,
        region: Optional[Tuple[int, int, int, int]] = None
    ) -> Optional[int]:
        """
        Read numeric value from screenshot.

        Optimized for reading numbers (resource counts, troop counts, etc.).

        Args:
            screenshot: Screenshot
            region: Region to read from

        Returns:
            Extracted number or None
        """
        try:
            # Use digits-only OCR mode
            config = r'--oem 3 --psm 7 digits'

            if region:
                x, y, w, h = region
                image = screenshot[y:y+h, x:x+w]
            else:
                image = screenshot

            # Preprocess
            image = self._preprocess_for_ocr(image)

            # OCR
            text = pytesseract.image_to_string(image, config=config)

            # Extract numbers
            numbers = ''.join(filter(str.isdigit, text))

            if numbers:
                return int(numbers)

            return None

        except Exception as e:
            self.logger.error(f"Error reading numbers: {e}")
            return None

    def _preprocess_for_ocr(self, image: np.ndarray) -> np.ndarray:
        """
        Preprocess image for better OCR accuracy.

        Applies:
        - Grayscale conversion
        - Thresholding
        - Noise reduction
        """
        try:
            # Convert to grayscale
            if len(image.shape) == 3:
                gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
            else:
                gray = image

            # Resize if too small (OCR works better on larger text)
            h, w = gray.shape
            if h < 30:
                scale = 30 / h
                new_w = int(w * scale)
                new_h = int(h * scale)
                gray = cv2.resize(gray, (new_w, new_h))

            # Apply thresholding
            # Try adaptive thresholding first
            processed = cv2.adaptiveThreshold(
                gray,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY,
                11,
                2
            )

            # Denoise
            processed = cv2.fastNlMeansDenoising(processed, h=10)

            return processed

        except Exception as e:
            self.logger.error(f"Preprocessing error: {e}")
            return image

    # ========================================================================
    # UI ELEMENT DETECTION
    # ========================================================================

    def find_button(
        self,
        screenshot: np.ndarray,
        button_name: str,
        confidence: float = 0.8
    ) -> Optional[Tuple[int, int]]:
        """
        Find button by name (convenience method).

        Looks for template file: templates/buttons/{button_name}.png

        Args:
            screenshot: Screenshot
            button_name: Button identifier
            confidence: Minimum confidence

        Returns:
            (x, y) center coordinates or None
        """
        template_path = self.templates_dir / "buttons" / f"{button_name}.png"

        if not template_path.exists():
            self.logger.warning(f"Button template not found: {template_path}")
            return None

        result = self.find_template(screenshot, str(template_path), confidence)

        if result.found:
            return result.location

        return None

    def check_screen(
        self,
        screenshot: np.ndarray,
        screen_name: str,
        confidence: float = 0.7
    ) -> bool:
        """
        Check if we're on a specific screen.

        Looks for template: templates/screens/{screen_name}.png

        Args:
            screenshot: Screenshot
            screen_name: Screen identifier
            confidence: Minimum confidence

        Returns:
            True if on that screen
        """
        template_path = self.templates_dir / "screens" / f"{screen_name}.png"

        if not template_path.exists():
            self.logger.warning(f"Screen template not found: {template_path}")
            return False

        result = self.find_template(screenshot, str(template_path), confidence)
        return result.found

    def wait_for_element(
        self,
        adb,
        template_path: str,
        timeout_seconds: int = 10,
        check_interval: float = 0.5
    ) -> Optional[Tuple[int, int]]:
        """
        Wait for element to appear on screen.

        Useful for waiting after actions.

        Args:
            adb: ADBConnection instance
            template_path: Template to wait for
            timeout_seconds: How long to wait
            check_interval: How often to check

        Returns:
            Element location or None if timeout
        """
        import time
        start_time = time.time()

        while (time.time() - start_time) < timeout_seconds:
            screenshot = adb.capture_screen()
            if screenshot is None:
                continue

            result = self.find_template(screenshot, template_path)

            if result.found:
                return result.location

            time.sleep(check_interval)

        self.logger.warning(f"Element not found after {timeout_seconds}s timeout")
        return None

    # ========================================================================
    # COLOR DETECTION
    # ========================================================================

    def find_color(
        self,
        screenshot: np.ndarray,
        color_bgr: Tuple[int, int, int],
        tolerance: int = 10
    ) -> List[Tuple[int, int]]:
        """
        Find all pixels matching a color.

        Useful for finding colored markers, resource nodes, etc.

        Args:
            screenshot: Screenshot
            color_bgr: Color to find (B, G, R)
            tolerance: Color matching tolerance

        Returns:
            List of (x, y) coordinates
        """
        try:
            # Create color range
            lower = np.array([max(0, c - tolerance) for c in color_bgr])
            upper = np.array([min(255, c + tolerance) for c in color_bgr])

            # Create mask
            mask = cv2.inRange(screenshot, lower, upper)

            # Find coordinates
            coords = np.column_stack(np.where(mask > 0))

            # Convert to (x, y) format
            points = [(int(x), int(y)) for y, x in coords]

            return points

        except Exception as e:
            self.logger.error(f"Color detection error: {e}")
            return []

    # ========================================================================
    # UTILITY METHODS
    # ========================================================================

    def _load_template(self, template_path: str) -> Optional[np.ndarray]:
        """
        Load template image with caching.

        Args:
            template_path: Path to template file

        Returns:
            Template as numpy array or None
        """
        # Check cache
        if template_path in self._template_cache:
            return self._template_cache[template_path]

        # Load template
        try:
            template = cv2.imread(template_path)

            if template is None:
                self.logger.error(f"Failed to load template: {template_path}")
                return None

            # Cache it
            self._template_cache[template_path] = template

            return template

        except Exception as e:
            self.logger.error(f"Error loading template: {e}")
            return None

    def save_debug_image(
        self,
        screenshot: np.ndarray,
        result: MatchResult,
        output_path: str
    ):
        """
        Save screenshot with match highlighted (for debugging).

        Args:
            screenshot: Screenshot
            result: Match result
            output_path: Where to save
        """
        if not result.found or not result.bbox:
            return

        try:
            # Draw rectangle around match
            img_copy = screenshot.copy()
            x, y, w, h = result.bbox
            cv2.rectangle(img_copy, (x, y), (x + w, y + h), (0, 255, 0), 2)

            # Add confidence text
            text = f"{result.confidence:.2f}"
            cv2.putText(img_copy, text, (x, y - 10),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

            cv2.imwrite(output_path, img_copy)
            self.logger.info(f"Debug image saved to {output_path}")

        except Exception as e:
            self.logger.error(f"Error saving debug image: {e}")

    def clear_template_cache(self):
        """Clear template cache (free memory)"""
        self._template_cache.clear()
        self.logger.info("Template cache cleared")

    def __repr__(self) -> str:
        return f"ScreenAnalyzer(templates={len(self._template_cache)} cached)"
