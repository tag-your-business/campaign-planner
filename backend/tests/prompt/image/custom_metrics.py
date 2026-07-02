"""Custom metrics for image generation evaluation."""

import base64
import json
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


JUDGE_INSTRUCTIONS = """\
You are verifying text placement in a generated social media image.

Below is the TEXT section of the prompt that produced the image, followed by the image
itself. Answer these checks by looking at the image:

1. website_address_bottom: If the prompt asked for a website and/or address along the
   bottom edge, is that text rendered as a line along the bottom edge of the frame?
2. phone_email_top_right: If the prompt asked for a phone number and/or email in the
   top right corner, is that text rendered in the top right corner?
3. no_stray_contact_text: Contact details (website, address, phone, email) do NOT
   appear anywhere other than their pinned positions.

For each check answer "pass", "fail", or "not_applicable" (use not_applicable when the
prompt did not request that element). Respond with ONLY a JSON object:
{"website_address_bottom": "...", "phone_email_top_right": "...",
"no_stray_contact_text": "...", "notes": "one short sentence"}

Prompt TEXT requirements:
"""


class TextPlacementMetric(BaseMetric):
    """Vision-judge check that contact text landed where the prompt pinned it."""

    CHECKS = [
        "website_address_bottom",
        "phone_email_top_right",
        "no_stray_contact_text",
    ]

    def __init__(self, threshold: float = 0.7, judge_model: str = "gpt-4o"):
        self.threshold = threshold
        self.judge_model = judge_model

    def measure(self, test_case: LLMTestCase) -> float:
        image_path = test_case.actual_output

        if not image_path or not Path(image_path).exists():
            self.score = 0.0
            self.reason = f"Image file does not exist: {image_path}"
            self.success = False
            return self.score

        try:
            verdict = self._judge(Path(image_path), test_case.input or "")
        except Exception as e:
            self.score = 0.0
            self.reason = f"Vision judge call failed: {e}"
            self.success = False
            return self.score

        passed = [c for c in self.CHECKS if verdict.get(c) == "pass"]
        failed = [c for c in self.CHECKS if verdict.get(c) == "fail"]
        applicable = passed + failed

        if not applicable:
            self.score = 1.0
            self.reason = "No contact text requested — nothing to verify"
        else:
            self.score = len(passed) / len(applicable)
            notes = verdict.get("notes", "")
            if failed:
                self.reason = f"Failed checks: {', '.join(failed)}. {notes}"
            else:
                self.reason = f"All applicable placement checks passed. {notes}"

        self.success = self.score >= self.threshold
        return self.score

    def _judge(self, image_path: Path, image_prompt: str) -> dict:
        from openai import OpenAI

        image_b64 = base64.b64encode(image_path.read_bytes()).decode()
        judge_prompt = JUDGE_INSTRUCTIONS + image_prompt

        client = OpenAI()
        response = client.chat.completions.create(
            model=self.judge_model,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": judge_prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/png;base64,{image_b64}"},
                        },
                    ],
                }
            ],
            response_format={"type": "json_object"},
            temperature=0,
        )
        return json.loads(response.choices[0].message.content)

    async def a_measure(self, test_case: LLMTestCase) -> float:
        return self.measure(test_case)

    def is_successful(self) -> bool:
        return self.success

    @property
    def __name__(self):
        return "Text Placement"
