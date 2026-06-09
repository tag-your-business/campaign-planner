"""API endpoints for campaign management."""

import json
import logging
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from app.common.storage.service import StorageService
from app.core.config import settings
from app.features.publishing.service import PublisherService
from app.schedulers.generate_scheduler import run_generate_job

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/campaigns", tags=["campaigns"])


class CampaignResponse(BaseModel):
    """Campaign response model."""

    id: str
    company_name: str
    event_name: str
    status: str
    generated_at: Optional[str] = None
    scheduled_publish_date: Optional[str] = None


@router.post("/generate")
def trigger_generate():
    """
    Manually trigger campaign generation job.

    This endpoint runs the generation pipeline immediately,
    regardless of the scheduled cron time.
    """
    try:
        logger.info("Manual generation triggered via API")
        run_generate_job()
        return {"status": "success", "message": "Generation job completed"}
    except Exception as e:
        logger.error(f"Manual generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/publish")
async def trigger_publish():
    """
    Manually trigger campaign publishing job.

    This endpoint publishes all pending campaigns immediately,
    regardless of their scheduled publish date.
    """
    try:
        logger.info("Manual publish triggered via API")
        storage = StorageService()
        publisher = PublisherService()

        pending = storage.get_pending()
        logger.info(f"Found {len(pending)} pending campaigns")

        results = []
        for campaign in pending:
            try:
                await publisher.publish(campaign)
                results.append(
                    {"campaign_id": campaign.get("id"), "status": "success"}
                )
            except Exception as exc:
                logger.error(
                    f"Failed to publish campaign {campaign.get('id')}: {exc}"
                )
                results.append(
                    {
                        "campaign_id": campaign.get("id"),
                        "status": "failed",
                        "error": str(exc),
                    }
                )

        return {
            "status": "completed",
            "total": len(pending),
            "results": results,
        }
    except Exception as e:
        logger.error(f"Manual publish failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/pending", response_model=list[CampaignResponse])
def get_pending_campaigns():
    """
    Get all pending campaigns.

    Returns a list of campaigns that have been generated but not yet published.
    """
    try:
        storage = StorageService()
        pending = storage.get_pending()

        return [
            CampaignResponse(
                id=c.get("id", ""),
                company_name=c.get("company_name", ""),
                event_name=c.get("event_name", ""),
                status=c.get("status", ""),
                generated_at=c.get("generated_at"),
                scheduled_publish_date=c.get("scheduled_publish_date"),
            )
            for c in pending
        ]
    except Exception as e:
        logger.error(f"Failed to get pending campaigns: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{campaign_id}")
def get_campaign(campaign_id: str):
    """
    Get campaign details by ID.

    Returns full campaign metadata including paths to generated assets.
    """
    try:
        metadata_path = (
            Path(settings.campaigns_dir)
            / "generated"
            / campaign_id
            / "metadata.json"
        )

        if not metadata_path.exists():
            raise HTTPException(
                status_code=404, detail=f"Campaign {campaign_id} not found"
            )

        metadata = json.loads(metadata_path.read_text())
        return metadata
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/{campaign_id}/publish")
async def publish_campaign(campaign_id: str):
    """
    Publish a specific campaign by ID.

    This endpoint publishes a single campaign immediately,
    regardless of its scheduled publish date.
    """
    try:
        # Get campaign metadata
        metadata_path = (
            Path(settings.campaigns_dir)
            / "generated"
            / campaign_id
            / "metadata.json"
        )

        if not metadata_path.exists():
            raise HTTPException(
                status_code=404, detail=f"Campaign {campaign_id} not found"
            )

        campaign = json.loads(metadata_path.read_text())

        # Check if already published
        if campaign.get("status") == "published":
            return {
                "status": "already_published",
                "message": f"Campaign {campaign_id} is already published",
            }

        # Publish
        publisher = PublisherService()
        await publisher.publish(campaign)

        return {
            "status": "success",
            "message": f"Campaign {campaign_id} published successfully",
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to publish campaign {campaign_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
