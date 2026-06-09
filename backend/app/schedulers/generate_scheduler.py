"""Cron job: for each registered company + upcoming events, run the generation pipeline."""

import json
import logging
from datetime import datetime, timedelta
from pathlib import Path

from app.common.storage.service import StorageService
from app.core.config import settings
from app.features.generation.branding import BrandingService
from app.features.generation.caption import CaptionGenerator
from app.features.generation.image import ImageService
from app.features.generation.planner import CampaignPlanner
from app.features.generation.prompt import PromptGenerator

logger = logging.getLogger(__name__)


def generate_campaign_id(company_slug: str, event_id: str) -> str:
    """Generate a unique campaign ID."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{company_slug}_{event_id}_{timestamp}"


def run_generate_job() -> None:
    """
    Main generation job pipeline.

    1. Load all active companies from registry
    2. Get events for next 30 days
    3. Filter events that are X days away (generation lead time)
    4. For each company-event pair:
       - Plan campaign (check relevance)
       - Generate caption via GPT
       - Generate image prompt
       - Generate image via DALL-E
       - Apply branding
       - Save to filesystem with metadata
       - Set status to "pending"
    5. Error isolation: log failures but continue processing
    """
    logger.info("Generate scheduler started")

    try:
        # Initialize services
        storage = StorageService()
        planner = CampaignPlanner()
        caption_gen = CaptionGenerator()
        prompt_gen = PromptGenerator()
        image_service = ImageService()
        branding_service = BrandingService()

        # 1. Load all active companies
        companies = load_active_companies()
        logger.info(f"Loaded {len(companies)} active companies")

        # 2. Get upcoming events (next 30 days)
        events = load_upcoming_events(days=30)
        logger.info(f"Loaded {len(events)} upcoming events")

        # 3. Filter events that should be generated now (X days before event)
        generation_date = datetime.now() + timedelta(
            days=settings.generation_lead_days
        )
        events_to_generate = [
            e
            for e in events
            if abs(
                (datetime.fromisoformat(e["date"]) - generation_date).days
            )
            <= 1
        ]
        logger.info(
            f"Found {len(events_to_generate)} events to generate "
            f"(~{settings.generation_lead_days} days out)"
        )

        # 4. Process each company-event pair
        generated_count = 0
        failed_count = 0

        for company in companies:
            for event in events_to_generate:
                try:
                    # Plan campaign (checks relevance)
                    campaign_spec = planner.plan(company, event)

                    if campaign_spec is None:
                        # Event not relevant for this company
                        continue

                    # Generate campaign ID
                    campaign_id = generate_campaign_id(
                        company["slug"], event["id"]
                    )
                    campaign_dir = (
                        Path(settings.campaigns_dir)
                        / "generated"
                        / campaign_id
                    )
                    campaign_dir.mkdir(parents=True, exist_ok=True)

                    logger.info(
                        f"Generating campaign: {company['name']} - {event['name']}"
                    )

                    # Generate caption
                    caption = caption_gen.generate(campaign_spec)
                    caption_path = campaign_dir / "caption.txt"
                    caption_path.write_text(caption)

                    # Generate image prompt
                    image_prompt = prompt_gen.generate(campaign_spec)

                    # Generate image via DALL-E
                    raw_image_path = campaign_dir / "image_raw.png"
                    image_service.generate(image_prompt, raw_image_path)

                    # Apply branding
                    logo_path = (
                        Path(settings.companies_dir)
                        / company["slug"]
                        / "logo.png"
                    )
                    final_image_path = campaign_dir / "image.png"
                    branding_service.apply(
                        raw_image_path,
                        logo_path if logo_path.exists() else None,
                        final_image_path,
                    )

                    # Save metadata
                    metadata = {
                        "id": campaign_id,
                        "company_slug": company["slug"],
                        "company_name": company["name"],
                        "event_id": event["id"],
                        "event_name": event["name"],
                        "event_date": event["date"],
                        "generated_at": datetime.now().isoformat(),
                        "scheduled_publish_date": campaign_spec[
                            "scheduled_publish_date"
                        ],
                        "status": "pending",
                        "caption": caption,
                        "image_path": str(final_image_path),
                        "platforms": campaign_spec["platforms"],
                        "facebook_page_id": campaign_spec.get(
                            "facebook_page_id", ""
                        ),
                        "instagram_account_id": campaign_spec.get(
                            "instagram_account_id", ""
                        ),
                    }

                    storage.save_metadata(campaign_id, metadata)
                    generated_count += 1

                    logger.info(
                        f"Successfully generated campaign {campaign_id}"
                    )

                except Exception as exc:
                    failed_count += 1
                    logger.error(
                        f"Failed to generate campaign for {company['name']} - "
                        f"{event['name']}: {exc}",
                        exc_info=True,
                    )
                    # Continue with next campaign

        logger.info(
            f"Generate job completed: {generated_count} succeeded, "
            f"{failed_count} failed"
        )

    except Exception as exc:
        logger.error(f"Generate job failed: {exc}", exc_info=True)


def load_active_companies() -> list[dict]:
    """Load all active companies from the registry."""
    registry_path = Path(settings.registry_path)

    if not registry_path.exists():
        logger.warning(f"Registry not found: {registry_path}")
        return []

    registry = json.loads(registry_path.read_text())
    active_companies = [c for c in registry if c.get("active", False)]

    # Load full profiles
    companies = []
    for entry in active_companies:
        slug = entry["slug"]
        profile_path = (
            Path(settings.companies_dir) / slug / "profile.json"
        )

        if profile_path.exists():
            profile = json.loads(profile_path.read_text())
            companies.append(profile)
        else:
            logger.warning(f"Profile not found for {slug}")

    return companies


def load_upcoming_events(days: int = 30) -> list[dict]:
    """Load events for the next X days."""
    current_year = datetime.now().year
    events_path = Path(settings.events_dir) / f"{current_year}.json"

    if not events_path.exists():
        logger.warning(f"Events file not found: {events_path}")
        return []

    all_events = json.loads(events_path.read_text())

    # Filter for upcoming events
    now = datetime.now()
    future_date = now + timedelta(days=days)

    upcoming = [
        e
        for e in all_events
        if now <= datetime.fromisoformat(e["date"]) <= future_date
    ]

    return upcoming
