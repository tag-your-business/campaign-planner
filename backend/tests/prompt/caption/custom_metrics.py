"""Custom metrics for caption evaluation."""

import re

from deepeval.metrics import BaseMetric
from deepeval.test_case import LLMTestCase


class CaptionLengthMetric(BaseMetric):
    """Validates caption length is within bounds."""

    def __init__(self, min_length: int = 150, max_length: int = 300):
        self.min_length = min_length
        self.max_length = max_length
        self.threshold = 1.0

    def measure(self, test_case: LLMTestCase) -> float:
        caption = test_case.actual_output
        length = len(caption)

        if self.min_length <= length <= self.max_length:
            self.score = 1.0
            self.reason = f"Caption length {length} is within range"
            self.success = True
        else:
            self.score = 0.0
            self.reason = (
                f"Caption length {length} outside range "
                f"[{self.min_length}, {self.max_length}]"
            )
            self.success = False

        return self.score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        return self.measure(test_case)

    def is_successful(self) -> bool:
        return self.success

    @property
    def __name__(self):
        return "Caption Length"


class HashtagQualityMetric(BaseMetric):
    """Validates hashtag count is within bounds."""

    def __init__(self, min_count: int = 3, max_count: int = 5):
        self.min_count = min_count
        self.max_count = max_count
        self.threshold = 1.0

    def measure(self, test_case: LLMTestCase) -> float:
        caption = test_case.actual_output
        hashtags = re.findall(r"#\w+", caption)
        count = len(hashtags)

        if self.min_count <= count <= self.max_count:
            self.score = 1.0
            self.reason = f"Found {count} hashtags (valid range)"
            self.success = True
        else:
            self.score = 0.0
            self.reason = (
                f"Found {count} hashtags, expected {self.min_count}-{self.max_count}"
            )
            self.success = False

        return self.score

    async def a_measure(self, test_case: LLMTestCase) -> float:
        return self.measure(test_case)

    def is_successful(self) -> bool:
        return self.success

    @property
    def __name__(self):
        return "Hashtag Count"
