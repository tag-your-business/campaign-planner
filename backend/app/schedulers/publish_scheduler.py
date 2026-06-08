"""Cron job: pick up pending campaigns from storage and publish them."""
import logging

from app.common.storage.service import StorageService
from app.features.publishing.service import PublisherService

logger = logging.getLogger(__name__)


def run_publish_job() -> None:
    logger.info("Publish scheduler started")
    storage = StorageService()
    publisher = PublisherService()
    pending = storage.get_pending()
    logger.info(f"Found {len(pending)} pending campaigns")
    for campaign in pending:
        try:
            publisher.publish(campaign)
        except Exception as exc:
            logger.error(f"Failed to publish campaign {campaign.get('id')}: {exc}")
