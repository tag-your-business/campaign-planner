import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


class MockInstagramPublisher:
    """Mock Instagram publisher for testing."""

    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.published_campaigns = []

    async def publish(self, campaign: Dict[str, Any]) -> Dict[str, Any]:
        """Simulate Instagram publishing."""
        if self.should_fail:
            logger.error(f"Mock: Failed to publish to Instagram: {campaign['id']}")
            raise Exception("Mock Instagram API error")

        print(f"✓ Mock: Published to Instagram - Campaign: {campaign['id']}")
        print(f"  Caption: {campaign.get('caption', '')}")
        logger.info(f"Mock: Published to Instagram - Campaign: {campaign['id']}")

        self.published_campaigns.append(campaign)

        return {
            "status": "success",
            "platform": "instagram",
            "post_id": f"ig_mock_{campaign['id']}",
        }
