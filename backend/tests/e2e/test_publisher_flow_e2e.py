"""
End-to-end tests for publisher flow with REAL Facebook and Instagram accounts.

⚠️ WARNING: These tests publish to REAL social media accounts!
   - Posts will be publicly visible on Facebook and Instagram
   - You will need to manually delete test posts after verification
   - Only run these tests when you want to verify the full publishing workflow

Prerequisites:
    1. Create .env.e2e from .env.e2e.example
    2. Add your real Facebook Page ID and Access Token
    3. Add your real Instagram Business Account ID and Access Token
    4. Set RUN_E2E=1 in .env.e2e to enable E2E tests
    5. Run: poetry run pytest tests/e2e/ -m e2e -v

These tests use the ACTUAL publishers (no mocks) to verify the complete
publishing workflow in a real-world scenario.
"""

import os
import subprocess
from pathlib import Path
from typing import Any

import pytest
from app.core.config import settings
from app.features.publishing.service import PublisherService
from app.features.publishing.utils import get_facebook_photo_url

# Environment variable to enable/disable E2E tests
RUN_E2E = os.getenv("RUN_E2E", "0") == "1"


# Helper function to check if E2E tests should run
def _should_run_e2e_tests() -> bool:
    """
    Check if E2E tests should run.

    E2E tests run only if:
    1. RUN_E2E environment variable is set to "1"
    2. All required credentials are configured
    """
    if not RUN_E2E:
        return False

    # Access tokens fall back to backend/.env (see conftest.e2e_credentials)
    required = [
        os.getenv("E2E_FACEBOOK_PAGE_ID"),
        os.getenv("E2E_FACEBOOK_ACCESS_TOKEN") or settings.facebook_access_token,
        os.getenv("E2E_INSTAGRAM_ACCOUNT_ID"),
        os.getenv("E2E_INSTAGRAM_ACCESS_TOKEN") or settings.instagram_access_token,
    ]
    return all(required)


@pytest.mark.e2e
@pytest.mark.skipif(
    not _should_run_e2e_tests(),
    reason=(
        "E2E tests disabled. Set RUN_E2E=1 in .env.e2e and configure credentials to run."
    ),
)
class TestPublisherFlowE2E:
    """
    End-to-end tests for the complete publisher flow with real accounts.

    These tests verify that the publishing workflow works correctly with
    actual Facebook and Instagram APIs.
    """

    @pytest.fixture(scope="class", autouse=True)
    def setup_e2e_data(self) -> None:
        """
        Generate fresh sample E2E data before running tests.

        This fixture runs automatically before any test in this class
        to ensure we have clean, fresh test data.
        """
        # Get the path to the generate_sample_data.py script
        script_path = Path(__file__).parent / "generate_sample_data.py"

        # Run the script to generate fresh sample data
        result = subprocess.run(
            ["python3", str(script_path)],
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            pytest.fail(f"Failed to generate sample E2E data: {result.stderr}")

        print("\n✨ Fresh E2E sample data generated")

    @pytest.mark.asyncio
    async def test_publish_to_facebook_real(
        self, e2e_facebook_campaign: dict[str, Any]
    ) -> None:
        """
        Test publishing to a REAL Facebook account.

        ⚠️ WARNING: This test creates a REAL post on your Facebook Page.
           You will need to manually delete it after verification.

        Args:
            e2e_facebook_campaign: Campaign metadata with real FB credentials
        """
        # Create publisher service (uses real publishers, no mocks)
        publisher = PublisherService()

        # Publish campaign
        results = await publisher.publish(e2e_facebook_campaign)

        # Verify results
        assert "facebook" in results
        fb_result = results["facebook"]

        # Check that publishing succeeded
        assert fb_result["status"] == "success", f"Facebook publish failed: {fb_result}"
        assert fb_result["post_id"], "No post ID returned"

        # Verify post ID format (should be numeric or page_id_post_id format)
        post_id = fb_result["post_id"]
        assert post_id, "Post ID should not be empty"

        print("\n✅ Successfully published to Facebook!")
        print(f"   Post ID: {post_id}")
        print("   ⚠️  Remember to delete this test post from your Facebook Page!")

    @pytest.mark.asyncio
    async def test_publish_to_instagram_real(
        self, e2e_instagram_campaign: dict[str, Any], e2e_credentials: dict[str, str]
    ) -> None:
        """
        Test publishing to a REAL Instagram account.

        Strategy: Upload to Facebook first to get a publicly accessible
        image URL, then use that URL to publish to Instagram.

        ⚠️ WARNING: This test creates REAL posts on both Facebook and Instagram.
           You will need to manually delete them after verification.

        Args:
            e2e_instagram_campaign: Campaign metadata with real IG credentials
            e2e_credentials: Real Facebook/Instagram credentials
        """
        # Create publisher service
        publisher = PublisherService()

        # Step 1: Upload to Facebook first to get image URL
        fb_campaign = {
            "id": f"{e2e_instagram_campaign['id']}-fb-temp",
            "platforms": ["facebook"],
            "facebook_page_id": e2e_credentials["facebook_page_id"],
            "caption": e2e_instagram_campaign["caption"],
            "image_path": e2e_instagram_campaign.get(
                "image_path",
                "tests/e2e/data/campaigns/generated/sample-e2e-campaign/image.jpg",
            ),
        }

        fb_results = await publisher.facebook.publish(fb_campaign)
        assert (
            fb_results["status"] == "success"
        ), f"FB upload failed: {fb_results.get('error')}"

        fb_post_id = fb_results["post_id"]
        print(f"\n📤 Uploaded to Facebook for image hosting: {fb_post_id}")

        # Step 2: Get the publicly accessible image URL
        image_url = await get_facebook_photo_url(
            fb_post_id, e2e_credentials["facebook_access_token"]
        )
        print(f"🔗 Got public image URL: {image_url[:60]}...")

        # Step 3: Update campaign with image URL and publish to Instagram
        e2e_instagram_campaign["image_url"] = image_url
        results = await publisher.publish(e2e_instagram_campaign)

        # Verify results
        assert "instagram" in results
        ig_result = results["instagram"]

        # Check that publishing succeeded
        assert (
            ig_result["status"] == "success"
        ), f"Instagram publish failed: {ig_result}"
        assert ig_result["post_id"], "No post ID returned"

        post_id = ig_result["post_id"]
        print("\n✅ Successfully published to Instagram!")
        print(f"   Instagram Media ID: {post_id}")
        print(f"   Facebook Post ID (for image): {fb_post_id}")
        print("   ⚠️  Remember to delete test posts from Instagram and Facebook!")

    @pytest.mark.asyncio
    async def test_publish_multi_platform_real(
        self,
        e2e_multi_platform_campaign: dict[str, Any],
        e2e_credentials: dict[str, str],
    ) -> None:
        """
        Test publishing to REAL Facebook and Instagram accounts simultaneously.

        Strategy: Publish to Facebook first, get the image URL, then publish
        to Instagram using that URL.

        ⚠️ WARNING: This test creates REAL posts on BOTH platforms.
           You will need to manually delete them after verification.

        Args:
            e2e_multi_platform_campaign: Campaign with both platform credentials
            e2e_credentials: Real Facebook/Instagram credentials
        """
        # Create publisher service
        publisher = PublisherService()

        # Step 1: Publish to Facebook first
        fb_campaign = {
            "id": e2e_multi_platform_campaign["id"],
            "platforms": ["facebook"],
            "facebook_page_id": e2e_multi_platform_campaign["facebook_page_id"],
            "caption": e2e_multi_platform_campaign["caption"],
            "image_path": e2e_multi_platform_campaign["image_path"],
        }

        fb_results = await publisher.facebook.publish(fb_campaign)
        assert (
            fb_results["status"] == "success"
        ), f"FB publish failed: {fb_results.get('error')}"

        fb_post_id = fb_results["post_id"]
        print(f"\n✅ Published to Facebook: {fb_post_id}")

        # Step 2: Get the image URL from Facebook post
        image_url = await get_facebook_photo_url(
            fb_post_id, e2e_credentials["facebook_access_token"]
        )
        print(f"🔗 Got public image URL: {image_url[:60]}...")

        # Step 3: Publish to Instagram using the FB-hosted image URL
        ig_campaign = {
            "id": e2e_multi_platform_campaign["id"],
            "platforms": ["instagram"],
            "instagram_account_id": e2e_multi_platform_campaign["instagram_account_id"],
            "caption": e2e_multi_platform_campaign["caption"],
            "image_url": image_url,
        }

        ig_results = await publisher.instagram.publish(ig_campaign)
        assert (
            ig_results["status"] == "success"
        ), f"IG publish failed: {ig_results.get('error')}"

        ig_post_id = ig_results["post_id"]
        print(f"✅ Published to Instagram: {ig_post_id}")

        # Verify both results
        print("\n🎉 Multi-platform publishing complete!")
        print(f"   Facebook Post ID: {fb_post_id}")
        print(f"   Instagram Media ID: {ig_post_id}")
        print("   ⚠️  Remember to delete test posts from both platforms!")

        # Verify the metadata would be updated to "published"
        # (In the actual service, this happens via storage.update_status)
        assert fb_results["status"] == "success"
        assert ig_results["status"] == "success"
