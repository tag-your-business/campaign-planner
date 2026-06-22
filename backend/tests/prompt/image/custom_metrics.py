"""Custom metrics for image generation evaluation."""

from pathlib import Path

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase

try:
    import numpy as np
    from PIL import Image

    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class ImageGenerationSuccessMetric(BaseMetric):
    """Validates that an image was generated successfully."""

    def __init__(self, threshold: float = 1.0):
        self.threshold = threshold

    def measure(self, test_case: LLMTestCase) -> float:
        # The actual_output should contain the image path
        image_path = test_case.actual_output

        if not image_path:
            self.score = 0.0
            self.reason = "No image path provided"
            self.success = False
            return self.score

        path = Path(image_path)

        if not path.exists():
            self.score = 0.0
            self.reason = f"Image file does not exist: {image_path}"
            self.success = False
            return self.score

        # Check file size (should be non-zero)
        if path.stat().st_size == 0:
            self.score = 0.0
            self.reason = "Image file is empty (0 bytes)"
            self.success = False
            return self.score

        # Try to verify it's a valid image
        if PIL_AVAILABLE:
            try:
                with Image.open(path) as img:
                    img.verify()
                self.score = 1.0
                self.reason = f"Valid image generated: {path.name}"
                self.success = True
            except Exception as e:
                self.score = 0.0
                self.reason = f"Invalid image file: {e}"
                self.success = False
        else:
            # Without PIL, just check file exists and has size
            self.score = 1.0
            self.reason = (
                f"Image file exists: {path.name} ({path.stat().st_size} bytes)"
            )
            self.success = True

        return self.score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        return self.measure(test_case)

    def is_successful(self) -> bool:
        return self.success

    @property
    def __name__(self):
        return "Image Generation Success"


class VisualQualityScoreMetric(BaseMetric):
    """Basic quality checks for generated images (size, mode, variance)."""

    def __init__(
        self,
        threshold: float = 0.7,
        min_width: int = 512,
        min_height: int = 512,
        min_variance: float = 100.0,
    ):
        self.threshold = threshold
        self.min_width = min_width
        self.min_height = min_height
        self.min_variance = min_variance

    def measure(self, test_case: LLMTestCase) -> float:
        image_path = test_case.actual_output

        if not image_path:
            self.score = 0.0
            self.reason = "No image path provided"
            self.success = False
            return self.score

        path = Path(image_path)

        if not path.exists():
            self.score = 0.0
            self.reason = f"Image file does not exist: {image_path}"
            self.success = False
            return self.score

        if not PIL_AVAILABLE:
            self.score = 0.7
            self.reason = "PIL not available - basic check only (file exists)"
            self.success = True
            return self.score

        try:
            with Image.open(path) as img:
                width, height = img.size
                mode = img.mode

                checks_passed = 0
                total_checks = 3
                issues = []

                # Check 1: Minimum dimensions
                if width >= self.min_width and height >= self.min_height:
                    checks_passed += 1
                else:
                    issues.append(
                        f"Size {width}x{height} below minimum {self.min_width}x{self.min_height}"
                    )

                # Check 2: Color mode (should be RGB or RGBA)
                if mode in ("RGB", "RGBA"):
                    checks_passed += 1
                else:
                    issues.append(f"Unexpected color mode: {mode}")

                # Check 3: Image variance (not a solid color)
                img_array = np.array(img.convert("RGB"))
                variance = np.var(img_array)
                if variance >= self.min_variance:
                    checks_passed += 1
                else:
                    issues.append(f"Low variance ({variance:.1f}) - may be solid color")

                self.score = checks_passed / total_checks

                if self.score >= self.threshold:
                    self.reason = (
                        f"Quality checks passed: {checks_passed}/{total_checks}"
                    )
                    self.success = True
                else:
                    self.reason = f"Quality issues: {'; '.join(issues)}"
                    self.success = False

        except Exception as e:
            self.score = 0.0
            self.reason = f"Error analyzing image: {e}"
            self.success = False

        return self.score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        return self.measure(test_case)

    def is_successful(self) -> bool:
        return self.success

    @property
    def __name__(self):
        return "Visual Quality Score"
