"""
E2E test fixtures and configuration.

This module provides fixtures that inject real credentials from .env.e2e
into campaign metadata for end-to-end testing with actual Facebook and
Instagram accounts.
"""

import json
import os
from pathlib import Path
from typing import Any

import pytest
from app.core.config import settings
from dotenv import load_dotenv

# Load E2E environment variables from .env.e2e
e2e_env_path = Path(__file__).parent / ".env.e2e"
load_dotenv(e2e_env_path)


@pytest.fixture(scope="session")
def e2e_credentials() -> dict[str, str]:
    """
    Load E2E credentials from environment variables.

    Returns:
        Dictionary containing Facebook and Instagram credentials

    Raises:
        ValueError: If required credentials are missing
    """
    credentials = {
        "facebook_page_id": os.getenv("E2E_FACEBOOK_PAGE_ID", ""),
        "facebook_access_token": os.getenv("E2E_FACEBOOK_ACCESS_TOKEN", ""),
        "instagram_account_id": os.getenv("E2E_INSTAGRAM_ACCOUNT_ID", ""),
        "instagram_access_token": os.getenv("E2E_INSTAGRAM_ACCESS_TOKEN", ""),
    }

    # Check if any credential is missing
    missing = [key for key, value in credentials.items() if not value]
    if missing:
        raise ValueError(
            f"Missing E2E credentials: {', '.join(missing)}. "
            f"Please create {e2e_env_path} from .env.e2e.example and add your credentials."
        )

    return credentials


@pytest.fixture(scope="session")
def e2e_data_dir() -> Path:
    """Return the E2E test data directory path (generated campaigns)."""
    return Path(__file__).parent / "data" / "campaigns" / "generated"


@pytest.fixture(scope="session")
def e2e_campaigns_base_dir() -> Path:
    """Return the E2E campaigns base directory (for settings.campaigns_dir patch)."""
    return Path(__file__).parent / "data" / "campaigns"


@pytest.fixture
def e2e_base_metadata(e2e_data_dir: Path) -> dict[str, Any]:
    """
    Load base campaign metadata from sample E2E campaign.

    Args:
        e2e_data_dir: Path to E2E test data directory

    Returns:
        Base metadata dictionary
    """
    metadata_path = e2e_data_dir / "sample-e2e-campaign" / "metadata.json"
    with open(metadata_path, "r") as f:
        return json.load(f)


@pytest.fixture
def e2e_sample_image_path(e2e_data_dir: Path) -> Path:
    """
    Get path to sample E2E test image.

    Args:
        e2e_data_dir: Path to E2E test data directory

    Returns:
        Path to sample image
    """
    return e2e_data_dir / "sample-e2e-campaign" / "image.jpg"


@pytest.fixture
def e2e_facebook_campaign(
    e2e_base_metadata: dict[str, Any],
    e2e_sample_image_path: Path,
    e2e_credentials: dict[str, str],
    e2e_campaigns_base_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, Any]:
    """
    Create Facebook-only campaign metadata with real credentials.

    This fixture injects the actual Facebook Page ID and access token
    from environment variables into the campaign metadata.

    Args:
        e2e_base_metadata: Base metadata template
        e2e_sample_image_path: Path to test image
        e2e_credentials: Real Facebook/Instagram credentials
        e2e_campaigns_base_dir: Base campaigns directory for storage service
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        Campaign metadata with real Facebook credentials
    """
    # Patch settings to use E2E credentials and data directory
    monkeypatch.setattr(
        settings, "facebook_access_token", e2e_credentials["facebook_access_token"]
    )
    monkeypatch.setattr(settings, "campaigns_dir", str(e2e_campaigns_base_dir))

    # Create campaign metadata with real credentials
    metadata = e2e_base_metadata.copy()
    metadata["platforms"] = ["facebook"]
    metadata["facebook_page_id"] = e2e_credentials["facebook_page_id"]
    metadata["image_path"] = str(e2e_sample_image_path)

    # Remove Instagram fields for Facebook-only campaign
    metadata.pop("instagram_account_id", None)
    metadata.pop("image_url", None)

    return metadata


@pytest.fixture
def e2e_instagram_campaign(
    e2e_base_metadata: dict[str, Any],
    e2e_sample_image_path: Path,
    e2e_credentials: dict[str, str],
    e2e_campaigns_base_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, Any]:
    """
    Create Instagram-only campaign metadata with real credentials.

    This fixture injects the actual Instagram Account ID and access token
    from environment variables into the campaign metadata.

    Note: Instagram publishing requires a publicly accessible image URL.
    The test will upload to Facebook first, fetch the image URL, then use
    that URL for Instagram publishing.

    Args:
        e2e_base_metadata: Base metadata template
        e2e_sample_image_path: Path to test image
        e2e_credentials: Real Facebook/Instagram credentials
        e2e_campaigns_base_dir: Base campaigns directory for storage service
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        Campaign metadata with real Instagram credentials
    """
    # Patch settings to use E2E credentials (both FB and IG since test uploads to FB first)
    monkeypatch.setattr(
        settings, "facebook_access_token", e2e_credentials["facebook_access_token"]
    )
    monkeypatch.setattr(
        settings,
        "instagram_access_token",
        e2e_credentials["instagram_access_token"],
    )
    monkeypatch.setattr(settings, "campaigns_dir", str(e2e_campaigns_base_dir))

    # Create campaign metadata with real credentials
    metadata = e2e_base_metadata.copy()
    metadata["platforms"] = ["instagram"]
    metadata["instagram_account_id"] = e2e_credentials["instagram_account_id"]
    metadata["image_path"] = str(e2e_sample_image_path)
    # image_url will be set by the test after uploading to Facebook
    metadata["image_url"] = "PLACEHOLDER_SET_BY_TEST"

    # Keep facebook_page_id for the initial FB upload in the test
    metadata["facebook_page_id"] = e2e_credentials["facebook_page_id"]

    return metadata


@pytest.fixture
def e2e_multi_platform_campaign(
    e2e_base_metadata: dict[str, Any],
    e2e_sample_image_path: Path,
    e2e_credentials: dict[str, str],
    e2e_campaigns_base_dir: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, Any]:
    """
    Create multi-platform campaign metadata with real credentials.

    This fixture injects actual Facebook and Instagram credentials
    from environment variables into the campaign metadata.

    Note: The test will publish to Facebook first to get the image URL,
    then use that URL for Instagram publishing.

    Args:
        e2e_base_metadata: Base metadata template
        e2e_sample_image_path: Path to test image
        e2e_credentials: Real Facebook/Instagram credentials
        e2e_campaigns_base_dir: Base campaigns directory for storage service
        monkeypatch: Pytest monkeypatch fixture

    Returns:
        Campaign metadata with real credentials for both platforms
    """
    # Patch settings to use E2E credentials and data directory
    monkeypatch.setattr(
        settings, "facebook_access_token", e2e_credentials["facebook_access_token"]
    )
    monkeypatch.setattr(
        settings,
        "instagram_access_token",
        e2e_credentials["instagram_access_token"],
    )
    monkeypatch.setattr(settings, "campaigns_dir", str(e2e_campaigns_base_dir))

    # Create campaign metadata with real credentials
    metadata = e2e_base_metadata.copy()
    metadata["platforms"] = ["facebook", "instagram"]
    metadata["facebook_page_id"] = e2e_credentials["facebook_page_id"]
    metadata["instagram_account_id"] = e2e_credentials["instagram_account_id"]
    metadata["image_path"] = str(e2e_sample_image_path)
    # image_url will be set by the test after uploading to Facebook
    metadata["image_url"] = "PLACEHOLDER_SET_BY_TEST"

    return metadata
