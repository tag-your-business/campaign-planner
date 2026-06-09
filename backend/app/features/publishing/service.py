"""Dispatches campaigns to platform publishers."""

import logging

from app.common.storage.service import StorageService
from app.features.publishing.publishers.facebook import FacebookPublisher
from app.features.publishing.publishers.instagram import InstagramPublisher

logger = logging.getLogger(__name__)


class PublisherService:
    """Orchestrates publishing campaigns to multiple social media platforms."""

    def __init__(self):
        self.facebook = FacebookPublisher()
        self.instagram = InstagramPublisher()
        self.storage = StorageService()

    async def publish(self, campaign: dict) -> dict:
        """
        Publish a campaign to all configured platforms.

        Args:
            campaign: Campaign metadata dict containing platforms, IDs, etc.

        Returns:
            Dictionary with publishing results for each platform
        """
        campaign_id = campaign["id"]
        platforms = campaign.get("platforms", [])
        results = {}

        try:
            # Publish to each platform
            if "facebook" in platforms:
                logger.info(f"Publishing {campaign_id} to Facebook")
                fb_result = await self.facebook.publish(campaign)
                results["facebook"] = fb_result

            if "instagram" in platforms:
                logger.info(f"Publishing {campaign_id} to Instagram")
                ig_result = await self.instagram.publish(campaign)
                results["instagram"] = ig_result

            # Check if all succeeded
            all_succeeded = all(
                r.get("status") == "success" for r in results.values()
            )

            if all_succeeded:
                self.storage.update_status(campaign_id, "published")
                logger.info(f"Campaign {campaign_id} published successfully")
            else:
                self.storage.update_status(campaign_id, "failed")
                logger.warning(
                    f"Campaign {campaign_id} partially failed: {results}"
                )

            return results

        except Exception as e:
            logger.error(f"Failed to publish campaign {campaign_id}: {e}")
            self.storage.update_status(campaign_id, "failed")
            raise
