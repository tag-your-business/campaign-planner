"""Facebook publisher using Graph API."""

import logging
from pathlib import Path

import httpx
from app.core.config import settings
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class FacebookPublisher:
    """Publishes campaign content to Facebook using the Graph API."""

    def __init__(self):
        """Initialize Facebook publisher with API configuration."""
        self.base_url = f"https://graph.facebook.com/{settings.facebook_api_version}"
        self.access_token = settings.facebook_access_token

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    async def publish(self, campaign: dict) -> dict:
        """
        Publish a campaign to Facebook.

        Args:
            campaign: Campaign dict containing:
                - facebook_page_id: Facebook page ID
                - caption: Post caption/message
                - image_path: Path to the image file

        Returns:
            Dictionary with publication result:
                {
                    "platform": "facebook",
                    "post_id": str,
                    "status": "success" | "failed",
                    "error": str (if failed)
                }
        """
        page_id = campaign.get("facebook_page_id")

        # Validate page ID
        if not page_id:
            logger.error("No Facebook page ID provided")
            return {
                "platform": "facebook",
                "status": "failed",
                "error": "No Facebook page ID configured",
            }

        # Validate access token
        if not self.access_token:
            logger.error("No Facebook access token configured")
            return {
                "platform": "facebook",
                "status": "failed",
                "error": "No Facebook access token configured",
            }

        try:
            # Get image path
            image_path = Path(campaign.get("image_path", ""))
            if not image_path.exists():
                raise FileNotFoundError(f"Image not found: {image_path}")

            # Prepare the API request
            url = f"{self.base_url}/{page_id}/photos"
            caption = campaign.get("caption", "")

            # Read image file
            with open(image_path, "rb") as image_file:
                files = {"source": image_file}
                data = {
                    "message": caption,
                    "access_token": self.access_token,
                }

                # Make the API request
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.post(url, data=data, files=files)

                    # Check response
                    if response.status_code == 200:
                        result = response.json()
                        post_id = result.get("id", "")

                        logger.info(f"Successfully published to Facebook: {post_id}")

                        return {
                            "platform": "facebook",
                            "post_id": post_id,
                            "status": "success",
                        }
                    else:
                        error_msg = response.text
                        logger.error(
                            f"Facebook API error: {response.status_code} - {error_msg}"
                        )
                        return {
                            "platform": "facebook",
                            "status": "failed",
                            "error": f"API error: {response.status_code}",
                        }

        except Exception as e:
            logger.error(f"Failed to publish to Facebook: {e}")
            return {
                "platform": "facebook",
                "status": "failed",
                "error": str(e),
            }
