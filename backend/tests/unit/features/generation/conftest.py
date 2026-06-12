"""Shared fixtures for generation unit tests."""

from unittest.mock import patch

import pytest


@pytest.fixture(autouse=True)
def no_retry_sleep():
    """Patch time.sleep so tenacity retry waits don't slow down tests."""
    with patch("time.sleep"):
        yield
