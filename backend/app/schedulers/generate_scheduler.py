"""Cron job: for each registered company + upcoming events, run the generation pipeline."""
import logging
from datetime import datetime

from app.features.events.service import EventService
from app.features.companies.service import CompanyService
from app.features.generation.planner import CampaignPlanner
from app.features.generation.content import ContentService
from app.features.generation.image import ImageService
from app.features.generation.branding import BrandingService
from app.common.storage.service import StorageService

logger = logging.getLogger(__name__)


def run_generate_job() -> None:
    logger.info("Generate scheduler started")
    # TODO: wire up full pipeline
    raise NotImplementedError
