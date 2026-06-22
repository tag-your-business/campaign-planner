"""Shared fixtures for prompt evaluation tests."""

from pathlib import Path

import pytest


@pytest.fixture(scope="session")
def prompt_tests_dir():
    """Get prompt tests root directory."""
    return Path(__file__).parent


@pytest.fixture
def temp_results_dir(tmp_path):
    """Temporary results directory for tests."""
    return tmp_path / "results"
