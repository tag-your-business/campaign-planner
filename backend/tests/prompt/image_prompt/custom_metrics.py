"""Custom metrics for image prompt evaluation."""

import re

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase


class StructureValidationMetric(BaseMetric):
    """Validates that the image prompt contains all 5 required sections."""

    REQUIRED_SECTIONS = ["SCENE", "SUBJECT", "DETAILS", "TEXT", "CONSTRAINTS"]

    def __init__(self, threshold: float = 1.0):
        self.threshold = threshold

    def measure(self, test_case: LLMTestCase) -> float:
        prompt = test_case.actual_output
        found_sections = []
        missing_sections = []

        for section in self.REQUIRED_SECTIONS:
            # Look for section header at start of line (case-insensitive)
            pattern = rf"^\s*{section}\s*:"
            if re.search(pattern, prompt, re.MULTILINE | re.IGNORECASE):
                found_sections.append(section)
            else:
                missing_sections.append(section)

        self.score = len(found_sections) / len(self.REQUIRED_SECTIONS)

        if self.score == 1.0:
            self.reason = "All 5 required sections found"
            self.success = True
        else:
            self.reason = f"Missing sections: {', '.join(missing_sections)}"
            self.success = False

        return self.score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        return self.measure(test_case)

    def is_successful(self) -> bool:
        return self.success

    @property
    def __name__(self):
        return "Structure Validation"


class BrandColorInclusionMetric(BaseMetric):
    """Validates that brand colors are referenced in the prompt."""

    def __init__(self, threshold: float = 1.0):
        self.threshold = threshold

    def measure(self, test_case: LLMTestCase) -> float:
        prompt = test_case.actual_output
        context = test_case.context or []

        # Extract brand colors from context (format: "brand_colors: #XXXXXX, #YYYYYY")
        brand_colors = []
        for ctx in context:
            if "brand_colors" in ctx.lower():
                # Find hex color codes
                hex_colors = re.findall(r"#[0-9A-Fa-f]{6}", ctx)
                brand_colors.extend(hex_colors)

        if not brand_colors:
            self.score = 1.0
            self.reason = "No brand colors specified in context"
            self.success = True
            return self.score

        # Check if colors are mentioned in the prompt
        found_colors = []
        for color in brand_colors:
            if color.lower() in prompt.lower():
                found_colors.append(color)

        self.score = len(found_colors) / len(brand_colors) if brand_colors else 1.0

        if self.score == 1.0:
            self.reason = f"All brand colors referenced: {', '.join(found_colors)}"
            self.success = True
        elif self.score > 0:
            missing = [c for c in brand_colors if c not in found_colors]
            found_count = len(found_colors)
            total_count = len(brand_colors)
            self.reason = (
                f"Found {found_count}/{total_count} colors. Missing: {missing}"
            )
            self.success = False
        else:
            self.reason = f"No brand colors found in prompt. Expected: {brand_colors}"
            self.success = False

        return self.score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        return self.measure(test_case)

    def is_successful(self) -> bool:
        return self.success

    @property
    def __name__(self):
        return "Brand Color Inclusion"


class TextElementInclusionMetric(BaseMetric):
    """Validates that TEXT section contains header and body elements."""

    def __init__(self, threshold: float = 1.0):
        self.threshold = threshold

    def measure(self, test_case: LLMTestCase) -> float:
        prompt = test_case.actual_output

        # Extract TEXT section content
        text_match = re.search(
            r"TEXT\s*:(.*?)(?=CONSTRAINTS|$)", prompt, re.IGNORECASE | re.DOTALL
        )

        if not text_match:
            self.score = 0.0
            self.reason = "TEXT section not found in prompt"
            self.success = False
            return self.score

        text_section = text_match.group(1)

        # Check for quoted strings (header and body text)
        quoted_strings = re.findall(r'"[^"]+"|"[^"]+"', text_section)

        if len(quoted_strings) >= 2:
            self.score = 1.0
            self.reason = (
                f"TEXT section contains {len(quoted_strings)} quoted text elements"
            )
            self.success = True
        elif len(quoted_strings) == 1:
            self.score = 0.5
            self.reason = (
                "TEXT section has only 1 quoted element (expected header + body)"
            )
            self.success = False
        else:
            self.score = 0.0
            self.reason = "TEXT section has no quoted text elements"
            self.success = False

        return self.score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        return self.measure(test_case)

    def is_successful(self) -> bool:
        return self.success

    @property
    def __name__(self):
        return "Text Element Inclusion"
