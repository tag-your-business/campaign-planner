import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class MockFacebookPublisher:
    """Mock Facebook publisher for testing."""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.published_campaigns = []

    async def publish(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate Facebook publishing."""
        if self.should_fail:
            logger.error(f"Mock: Failed to publish to Facebook: {campaign['id']}")
            raise Exception("Mock Facebook API error")

        print(f"✓ Mock: Published to Facebook - Campaign: {campaign['id']}")
        print(f"  Caption: {campaign.get('caption', '')}")
        logger.info(f"Mock: Published to Facebook - Campaign: {campaign['id']}")

        self.published_campaigns.append(campaign)

        return {
            "status": "success",
            "platform": "facebook",
            "post_id": f"fb_mock_{campaign['id']}",
        }
