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


def _load_existing_metadata(
    campaigns_dir: str, company_slug: str, event_id: str
) -> dict | None:
    """Return existing metadata dict for this company+event pair, or None."""
    prefix = f"{company_slug}_{event_id}_"
    base = Path(campaigns_dir) / "generated"
    if not base.exists():
        return None
    for d in base.iterdir():
        if d.is_dir() and d.name.startswith(prefix):
            meta_file = d / "metadata.json"
            if meta_file.exists():
                return json.loads(meta_file.read_text())
    return None


def _run_caption_step(
    caption_gen: CaptionGenerator,
    campaign_spec: dict,
    campaign_dir: Path,
    existing_metadata: dict | None,
) -> dict:
    """Generate caption if not already present. Writes caption.txt on success."""
    existing_caption = (existing_metadata or {}).get("caption", "")
    if existing_caption:
        logger.info("Caption already generated, skipping")
        return {"success": True, "data": existing_caption}
    try:
        caption = caption_gen.generate(campaign_spec)
        (campaign_dir / "caption.txt").write_text(caption)
        return {"success": True, "data": caption}
    except Exception as exc:
        logger.error(f"Caption step failed: {exc}", exc_info=True)
        return {"success": False, "data": ""}


def _run_prompt_step(
    prompt_gen: PromptGenerator,
    campaign_spec: dict,
    existing_metadata: dict | None,
) -> dict:
    """Generate DALL-E image prompt if not already present."""
    existing_prompt = (existing_metadata or {}).get("image_prompt", "")
    if existing_prompt:
        logger.info("Image prompt already generated, skipping")
        return {"success": True, "data": existing_prompt}
    try:
        image_prompt = prompt_gen.generate(campaign_spec)
        return {"success": True, "data": image_prompt}
    except Exception as exc:
        logger.error(f"Prompt step failed: {exc}", exc_info=True)
        return {"success": False, "data": ""}


def _run_image_step(
    image_service: ImageService,
    branding_service: BrandingService,
    image_prompt: str,
    campaign_dir: Path,
    logo_path: Path | None,
    existing_metadata: dict | None,
) -> dict:
    """Generate and brand image if not already present. Returns branded image path."""
    existing_image_path = (existing_metadata or {}).get("image_path", "")
    if existing_image_path and Path(existing_image_path).exists():
        logger.info("Image already generated, skipping")
        return {"success": True, "data": existing_image_path}
    if not image_prompt:
        logger.warning("Image step skipped: no image prompt available")
        return {"success": False, "data": ""}
    try:
        raw_image_path = campaign_dir / "image_raw.png"
        image_service.generate(image_prompt, raw_image_path)
        final_image_path = campaign_dir / "image.png"
        branding_service.apply(raw_image_path, logo_path, final_image_path)
        return {"success": True, "data": str(final_image_path)}
    except Exception as exc:
        logger.error(f"Image step failed: {exc}", exc_info=True)
        return {"success": False, "data": ""}


def _process_campaign(
    storage: StorageService,
    planner: CampaignPlanner,
    caption_gen: CaptionGenerator,
    prompt_gen: PromptGenerator,
    image_service: ImageService,
    branding_service: BrandingService,
    company: dict,
    event: dict,
) -> bool:
    """Run (or resume) generation for one company+event. Returns True when all steps succeed."""
    existing = _load_existing_metadata(
        settings.campaigns_dir, company["slug"], event["id"]
    )

    if existing and existing.get("caption") and existing.get("image_path"):
        logger.info(
            f"Skipping {company['name']} - {event['name']}: already fully generated"
        )
        return True

    campaign_spec = planner.plan(company, event)
    if campaign_spec is None:
        return True  # Not relevant for this company — not a failure

    if existing:
        campaign_id = existing["id"]
        logger.info(
            f"Resuming partial campaign {campaign_id} for {company['name']} - {event['name']}"
        )
    else:
        campaign_id = generate_campaign_id(company["slug"], event["id"])
        logger.info(
            f"Generating campaign {campaign_id} for {company['name']} - {event['name']}"
        )

    campaign_dir = Path(settings.campaigns_dir) / "generated" / campaign_id
    campaign_dir.mkdir(parents=True, exist_ok=True)

    caption_result = _run_caption_step(
        caption_gen, campaign_spec, campaign_dir, existing
    )
    prompt_result = _run_prompt_step(prompt_gen, campaign_spec, existing)

    logo_path = Path(settings.companies_dir) / company["slug"] / "logo.png"
    image_result = _run_image_step(
        image_service,
        branding_service,
        prompt_result["data"],
        campaign_dir,
        logo_path if logo_path.exists() else None,
        existing,
    )

    all_succeeded = (
        caption_result["success"]
        and prompt_result["success"]
        and image_result["success"]
    )

    metadata = {
        "id": campaign_id,
        "company_slug": company["slug"],
        "company_name": company["name"],
        "event_id": event["id"],
        "event_name": event["name"],
        "event_date": event["date"],
        "generated_at": (existing or {}).get(
            "generated_at", datetime.now().isoformat()
        ),
        "last_attempted_at": datetime.now().isoformat(),
        "scheduled_publish_date": campaign_spec["scheduled_publish_date"],
        "status": "pending" if all_succeeded else "partial",
        "caption": caption_result["data"],
        "image_prompt": prompt_result["data"],
        "image_path": image_result["data"],
        "platforms": campaign_spec["platforms"],
        "facebook_page_id": campaign_spec.get("facebook_page_id", ""),
        "instagram_account_id": campaign_spec.get("instagram_account_id", ""),
    }

    storage.save_metadata(campaign_id, metadata)

    if all_succeeded:
        logger.info(f"Successfully generated campaign {campaign_id}")
    else:
        failed_steps = [
            name
            for name, result in [
                ("caption", caption_result),
                ("image_prompt", prompt_result),
                ("image", image_result),
            ]
            if not result["success"]
        ]
        logger.warning(
            f"Campaign {campaign_id} partially generated; failed steps: {failed_steps}"
        )

    return all_succeeded


def run_generate_job() -> None:
    """
    Main generation job pipeline.

    1. Load all active companies from registry
    2. Get events for next 30 days
    3. Filter events that are X days away (generation lead time)
    4. For each company-event pair:
       - Load existing metadata (resume partial campaigns)
       - Run caption / prompt / image steps only if not already done
       - Always save metadata, using empty strings for failed steps
    5. Error isolation: log failures but continue processing
    """
    logger.info("Generate scheduler started")

    try:
        storage = StorageService()
        planner = CampaignPlanner()
        caption_gen = CaptionGenerator()
        prompt_gen = PromptGenerator()
        image_service = ImageService()
        branding_service = BrandingService()

        companies = load_active_companies()
        logger.info(f"Loaded {len(companies)} active companies")

        events = load_upcoming_events(days=30)
        logger.info(f"Loaded {len(events)} upcoming events")

        now = datetime.now()
        cutoff = now + timedelta(days=settings.generation_lead_days)
        events_to_generate = [
            e
            for e in events
            if now.date() <= datetime.fromisoformat(e["date"]).date() <= cutoff.date()
        ]
        logger.info(
            f"Found {len(events_to_generate)} events to generate "
            f"(within next {settings.generation_lead_days} days)"
        )

        generated_count = 0
        failed_count = 0

        for company in companies:
            for event in events_to_generate:
                try:
                    success = _process_campaign(
                        storage,
                        planner,
                        caption_gen,
                        prompt_gen,
                        image_service,
                        branding_service,
                        company,
                        event,
                    )
                    if success:
                        generated_count += 1
                    else:
                        failed_count += 1
                except Exception as exc:
                    failed_count += 1
                    logger.error(
                        f"Failed to process campaign for {company['name']} - "
                        f"{event['name']}: {exc}",
                        exc_info=True,
                    )

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

    companies = []
    for entry in active_companies:
        slug = entry["slug"]
        profile_path = Path(settings.companies_dir) / slug / "profile.json"

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

    now = datetime.now()
    future_date = now + timedelta(days=days)

    upcoming = [
        e for e in all_events if now <= datetime.fromisoformat(e["date"]) <= future_date
    ]

    return upcoming
