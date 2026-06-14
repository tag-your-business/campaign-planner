"""Dispatches campaigns to platform publishers."""

import logging

from app.common.storage.service import StorageService
from app.features.publishing.publishers.facebook import FacebookPublisher
from app.features.publishing.publishers.instagram import InstagramPublisher
from app.features.publishing.utils import get_facebook_photo_url

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

        This method publishes to each platform and tracks individual platform
        statuses. The overall campaign status is set to "published" only when
        ALL platforms succeed.

        Args:
            campaign: Campaign metadata dict containing platforms, IDs, etc.

        Returns:
            Dictionary with publishing results for each platform
        """
        campaign_id = campaign["id"]
        platforms = campaign.get("platforms", [])
        results = {}

        try:
            # Publish to each platform and update individual statuses
            if "facebook" in platforms:
                logger.info(f"Publishing {campaign_id} to Facebook")
                fb_result = await self.facebook.publish(campaign)
                results["facebook"] = fb_result

                # Update Facebook platform status
                platform_status = (
                    "published" if fb_result.get("status") == "success" else "failed"
                )
                post_id = (
                    fb_result.get("post_id") if platform_status == "published" else None
                )
                self.storage.update_platform_status(
                    campaign_id, "facebook", platform_status, post_id
                )

                # Fetch and store the Facebook image URL for Instagram publishing
                if platform_status == "published" and post_id:
                    try:
                        image_url = await get_facebook_photo_url(post_id)
                        self.storage.update_image_url(campaign_id, image_url)
                        logger.info(
                            f"Stored Facebook image URL for campaign {campaign_id}"
                        )
                    except Exception as e:
                        logger.warning(
                            f"Failed to fetch Facebook image URL for {campaign_id}: {e}"
                        )

            if "instagram" in platforms:
                logger.info(f"Publishing {campaign_id} to Instagram")
                ig_result = await self.instagram.publish(campaign)
                results["instagram"] = ig_result

                # Update Instagram platform status
                platform_status = (
                    "published" if ig_result.get("status") == "success" else "failed"
                )
                post_id = (
                    ig_result.get("post_id") if platform_status == "published" else None
                )
                self.storage.update_platform_status(
                    campaign_id, "instagram", platform_status, post_id
                )

            # Log final status (calculated automatically by storage service)
            all_succeeded = all(r.get("status") == "success" for r in results.values())
            if all_succeeded:
                logger.info(
                    f"Campaign {campaign_id} published successfully to all platforms"
                )
            else:
                logger.warning(f"Campaign {campaign_id} partially failed: {results}")

            return results

        except Exception as e:
            logger.error(f"Failed to publish campaign {campaign_id}: {e}")
            # Mark overall status as failed
            self.storage.update_status(campaign_id, "failed")
            raise
