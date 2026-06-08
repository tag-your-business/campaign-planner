"""Cron job: for each registered company + upcoming events, run the generation pipeline."""

import logging

logger = logging.getLogger(__name__)


def run_generate_job() -> None:
    logger.info("Generate scheduler started")
    # TODO: wire up full pipeline
    raise NotImplementedError
