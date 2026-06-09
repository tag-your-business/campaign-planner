"""Cron job: pick up pending campaigns from storage and publish them."""

import asyncio
import logging

from app.common.storage.service import StorageService
from app.features.publishing.service import PublisherService

logger = logging.getLogger(__name__)


def run_publish_job() -> None:
    """
    Publish all pending campaigns that are scheduled for today or earlier.

    This job runs on a cron schedule and publishes campaigns that are ready.
    """
    logger.info("Publish scheduler started")

    # Since APScheduler runs this synchronously, we need to create an event loop
    asyncio.run(_async_publish_job())


async def _async_publish_job() -> None:
    """Async implementation of the publish job."""
    storage = StorageService()
    publisher = PublisherService()

    pending = storage.get_pending()
    logger.info(f"Found {len(pending)} pending campaigns")

    published_count = 0
    failed_count = 0

    for campaign in pending:
        try:
            await publisher.publish(campaign)
            published_count += 1
            logger.info(
                f"Successfully published campaign {campaign.get('id')}"
            )
        except Exception as exc:
            failed_count += 1
            logger.error(
                f"Failed to publish campaign {campaign.get('id')}: {exc}",
                exc_info=True,
            )

    logger.info(
        f"Publish job completed: {published_count} succeeded, {failed_count} failed"
    )
