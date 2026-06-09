"""Instagram publisher using Graph API."""

import logging
from pathlib import Path
import httpx
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.config import settings

logger = logging.getLogger(__name__)


class InstagramPublisher:
    """Publishes campaign content to Instagram using the Graph API."""

    def __init__(self):
        """Initialize Instagram publisher with API configuration."""
        self.base_url = f"https://graph.facebook.com/{settings.instagram_api_version}"
        self.access_token = settings.instagram_access_token

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    async def publish(self, campaign: dict) -> dict:
        """
        Publish a campaign to Instagram.

        Instagram requires a 2-step process:
        1. Create a media container with the image URL
        2. Publish the container

        Args:
            campaign: Campaign dict containing:
                - instagram_account_id: Instagram business account ID
                - caption: Post caption
                - image_url: Publicly accessible image URL

        Returns:
            Dictionary with publication result:
                {
                    "platform": "instagram",
                    "post_id": str,
                    "status": "success" | "failed",
                    "error": str (if failed)
                }
        """
        account_id = campaign.get("instagram_account_id")

        # Validate account ID
        if not account_id:
            logger.error("No Instagram account ID provided")
            return {
                "platform": "instagram",
                "status": "failed",
                "error": "No Instagram account ID configured",
            }

        # Validate access token
        if not self.access_token:
            logger.error("No Instagram access token configured")
            return {
                "platform": "instagram",
                "status": "failed",
                "error": "No Instagram access token configured",
            }

        try:
            # Get image URL (must be publicly accessible)
            image_url = campaign.get("image_url")
            if not image_url:
                raise ValueError(
                    "Instagram requires a publicly accessible image_url. "
                    "For V1, upload to Facebook first and use that URL, "
                    "or implement a simple file server."
                )

            caption = campaign.get("caption", "")

            # Step 1: Create media container
            container_id = await self._create_media_container(
                account_id, image_url, caption
            )

            if not container_id:
                return {
                    "platform": "instagram",
                    "status": "failed",
                    "error": "Failed to create media container",
                }

            # Step 2: Publish the container
            media_id = await self._publish_media(account_id, container_id)

            if media_id:
                logger.info(
                    f"Successfully published to Instagram: {media_id}"
                )
                return {
                    "platform": "instagram",
                    "post_id": media_id,
                    "status": "success",
                }
            else:
                return {
                    "platform": "instagram",
                    "status": "failed",
                    "error": "Failed to publish media container",
                }

        except Exception as e:
            logger.error(f"Failed to publish to Instagram: {e}")
            return {
                "platform": "instagram",
                "status": "failed",
                "error": str(e),
            }

    async def _create_media_container(
        self, account_id: str, image_url: str, caption: str
    ) -> str | None:
        """
        Step 1: Create a media container.

        Returns:
            Container ID if successful, None otherwise
        """
        try:
            url = f"{self.base_url}/{account_id}/media"
            params = {
                "image_url": image_url,
                "caption": caption,
                "access_token": self.access_token,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, params=params)

                if response.status_code == 200:
                    result = response.json()
                    container_id = result.get("id")
                    logger.info(f"Created Instagram media container: {container_id}")
                    return container_id
                else:
                    logger.error(
                        f"Failed to create media container: {response.status_code} - {response.text}"
                    )
                    return None

        except Exception as e:
            logger.error(f"Error creating media container: {e}")
            return None

    async def _publish_media(
        self, account_id: str, container_id: str
    ) -> str | None:
        """
        Step 2: Publish the media container.

        Returns:
            Media ID if successful, None otherwise
        """
        try:
            url = f"{self.base_url}/{account_id}/media_publish"
            params = {
                "creation_id": container_id,
                "access_token": self.access_token,
            }

            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(url, params=params)

                if response.status_code == 200:
                    result = response.json()
                    media_id = result.get("id")
                    logger.info(f"Published Instagram media: {media_id}")
                    return media_id
                else:
                    logger.error(
                        f"Failed to publish media: {response.status_code} - {response.text}"
                    )
                    return None

        except Exception as e:
            logger.error(f"Error publishing media: {e}")
            return None
