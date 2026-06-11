import json

import pytest
from app.common.storage.service import StorageService
from app.features.publishing.service import PublisherService
from tests.mocks.mock_facebook_publisher import MockFacebookPublisher
from tests.mocks.mock_instagram_publisher import MockInstagramPublisher


@pytest.mark.asyncio
class TestPublisherFlowIntegration:
    """Integration tests for the complete publisher flow."""

    async def test_publish_facebook_only(
        self, sample_campaign_facebook, temp_data_dir, mocker, caplog
    ):
        """Test publishing to Facebook only with mock publisher."""
        # Setup
        mock_fb = MockFacebookPublisher()
        mock_ig = MockInstagramPublisher()

        # Patch publishers
        mocker.patch(
            "app.features.publishing.service.FacebookPublisher", return_value=mock_fb
        )
        mocker.patch(
            "app.features.publishing.service.InstagramPublisher", return_value=mock_ig
        )

        publisher_service = PublisherService()

        # Execute
        with caplog.at_level("INFO"):
            result = await publisher_service.publish(sample_campaign_facebook)

        # Verify
        assert "facebook" in result
        assert result["facebook"]["status"] == "success"

        # Check mock was called
        assert len(mock_fb.published_campaigns) == 1
        assert len(mock_ig.published_campaigns) == 0

        # Check logs
        assert "Published to Facebook" in caplog.text or "Publishing" in caplog.text
        assert sample_campaign_facebook["id"] in caplog.text

        # Check metadata was updated
        metadata_path = (
            temp_data_dir
            / "campaigns"
            / "generated"
            / sample_campaign_facebook["id"]
            / "metadata.json"
        )
        with open(metadata_path) as f:
            updated_metadata = json.load(f)

        assert updated_metadata["status"] == "published"

    async def test_publish_instagram_only(
        self, sample_campaign_instagram, temp_data_dir, mocker, caplog
    ):
        """Test publishing to Instagram only with mock publisher."""
        # Setup
        mock_fb = MockFacebookPublisher()
        mock_ig = MockInstagramPublisher()

        mocker.patch(
            "app.features.publishing.service.FacebookPublisher", return_value=mock_fb
        )
        mocker.patch(
            "app.features.publishing.service.InstagramPublisher", return_value=mock_ig
        )

        publisher_service = PublisherService()

        # Execute
        with caplog.at_level("INFO"):
            result = await publisher_service.publish(sample_campaign_instagram)

        # Verify
        assert "instagram" in result
        assert result["instagram"]["status"] == "success"

        # Check mock was called
        assert len(mock_ig.published_campaigns) == 1
        assert len(mock_fb.published_campaigns) == 0

        # Check logs
        assert "Published to Instagram" in caplog.text or "Publishing" in caplog.text

    async def test_publish_multi_platform(
        self, sample_campaign_multi_platform, temp_data_dir, mocker, caplog
    ):
        """Test publishing to both Facebook and Instagram."""
        # Setup
        mock_fb = MockFacebookPublisher()
        mock_ig = MockInstagramPublisher()

        mocker.patch(
            "app.features.publishing.service.FacebookPublisher", return_value=mock_fb
        )
        mocker.patch(
            "app.features.publishing.service.InstagramPublisher", return_value=mock_ig
        )

        publisher_service = PublisherService()

        # Execute
        with caplog.at_level("INFO"):
            result = await publisher_service.publish(sample_campaign_multi_platform)

        # Verify both platforms succeeded
        assert "facebook" in result
        assert "instagram" in result
        assert result["facebook"]["status"] == "success"
        assert result["instagram"]["status"] == "success"

        # Check both mocks were called
        assert len(mock_fb.published_campaigns) == 1
        assert len(mock_ig.published_campaigns) == 1

        # Check logs show both publishes
        assert "Published to Facebook" in caplog.text or "Publishing" in caplog.text
        assert "Published to Instagram" in caplog.text or "Publishing" in caplog.text

    async def test_publish_failure_handling(
        self, sample_campaign_facebook, temp_data_dir, mocker, caplog
    ):
        """Test failure handling when publisher fails."""
        # Setup with failing mock
        mock_fb = MockFacebookPublisher(should_fail=True)

        mocker.patch(
            "app.features.publishing.service.FacebookPublisher", return_value=mock_fb
        )

        publisher_service = PublisherService()

        # Execute and expect exception
        with pytest.raises(Exception) as exc_info:
            with caplog.at_level("ERROR"):
                await publisher_service.publish(sample_campaign_facebook)

        # Check error was logged
        assert "Failed to publish" in caplog.text or "Mock Facebook API error" in str(
            exc_info.value
        )

        # Check metadata status was updated to failed
        metadata_path = (
            temp_data_dir
            / "campaigns"
            / "generated"
            / sample_campaign_facebook["id"]
            / "metadata.json"
        )
        with open(metadata_path) as f:
            updated_metadata = json.load(f)

        assert updated_metadata["status"] == "failed"

    async def test_batch_publish_multiple_campaigns(
        self, sample_campaign_facebook, sample_campaign_instagram, temp_data_dir, mocker
    ):
        """Test batch publishing multiple pending campaigns."""
        # Setup
        storage_service = StorageService()
        mock_fb = MockFacebookPublisher()
        mock_ig = MockInstagramPublisher()

        mocker.patch(
            "app.features.publishing.service.FacebookPublisher", return_value=mock_fb
        )
        mocker.patch(
            "app.features.publishing.service.InstagramPublisher", return_value=mock_ig
        )

        publisher_service = PublisherService()

        # Get all pending campaigns
        pending = storage_service.get_pending()
        assert len(pending) == 2

        # Execute batch publish
        results = []
        for campaign in pending:
            result = await publisher_service.publish(campaign)
            results.append(result)

        # Verify both campaigns published
        assert len(results) == 2
        assert all(
            any(r.get("status") == "success" for r in result.values())
            for result in results
        )
        assert len(mock_fb.published_campaigns) == 1
        assert len(mock_ig.published_campaigns) == 1

        # Check no more pending campaigns
        pending_after = storage_service.get_pending()
        assert len(pending_after) == 0

    async def test_campaign_isolation(
        self, sample_campaign_facebook, sample_campaign_instagram, temp_data_dir, mocker
    ):
        """Test that one campaign failure doesn't affect others."""
        # Setup with failing Facebook, working Instagram
        mock_fb = MockFacebookPublisher(should_fail=True)
        mock_ig = MockInstagramPublisher(should_fail=False)

        mocker.patch(
            "app.features.publishing.service.FacebookPublisher", return_value=mock_fb
        )
        mocker.patch(
            "app.features.publishing.service.InstagramPublisher", return_value=mock_ig
        )

        publisher_service = PublisherService()

        # Publish both campaigns - FB should fail, IG should succeed
        fb_failed = False
        try:
            await publisher_service.publish(sample_campaign_facebook)
        except Exception:
            fb_failed = True

        ig_result = await publisher_service.publish(sample_campaign_instagram)

        # Verify: FB failed, IG succeeded
        assert fb_failed is True
        assert "instagram" in ig_result
        assert ig_result["instagram"]["status"] == "success"

        # Instagram should have published despite Facebook failure
        assert len(mock_ig.published_campaigns) == 1
