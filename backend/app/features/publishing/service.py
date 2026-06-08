"""Dispatches campaigns to platform publishers."""

from app.common.storage.service import StorageService
from app.features.publishing.publishers.facebook import FacebookPublisher
from app.features.publishing.publishers.instagram import InstagramPublisher


class PublisherService:
    def __init__(self):
        self.facebook = FacebookPublisher()
        self.instagram = InstagramPublisher()
        self.storage = StorageService()

    def publish(self, campaign: dict) -> None:
        campaign_id = campaign["id"]
        try:
            self.facebook.publish(campaign)
            self.instagram.publish(campaign)
            self.storage.update_status(campaign_id, "published")
        except Exception:
            self.storage.update_status(campaign_id, "failed")
            raise
