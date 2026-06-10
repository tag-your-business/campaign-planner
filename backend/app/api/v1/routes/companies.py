"""API endpoints for company management."""

import json
import logging
from pathlib import Path

from app.core.config import settings
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/companies", tags=["companies"])


class CompanyListItem(BaseModel):
    """Company list item model."""

    slug: str
    name: str
    active: bool


class CompanyProfile(BaseModel):
    """Company profile model."""

    slug: str
    name: str
    industry: str
    tone: str
    brand_colors: list[str]
    social: dict


@router.get("/", response_model=list[CompanyListItem])
def list_companies():
    """
    List all companies from the registry.

    Returns a list of all companies with their slug, name, and active status.
    """
    try:
        registry_path = Path(settings.registry_path)

        if not registry_path.exists():
            logger.warning(f"Registry not found: {registry_path}")
            return []

        registry = json.loads(registry_path.read_text())

        return [
            CompanyListItem(
                slug=c.get("slug", ""),
                name=c.get("name", ""),
                active=c.get("active", False),
            )
            for c in registry
        ]
    except Exception as e:
        logger.error(f"Failed to list companies: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{slug}", response_model=CompanyProfile)
def get_company(slug: str):
    """
    Get company profile by slug.

    Returns the full company profile including industry, tone,
    brand colors, and social media account IDs.
    """
    try:
        profile_path = Path(settings.companies_dir) / slug / "profile.json"

        if not profile_path.exists():
            raise HTTPException(status_code=404, detail=f"Company {slug} not found")

        profile = json.loads(profile_path.read_text())

        return CompanyProfile(
            slug=profile.get("slug", ""),
            name=profile.get("name", ""),
            industry=profile.get("industry", ""),
            tone=profile.get("tone", ""),
            brand_colors=profile.get("brand_colors", []),
            social=profile.get("social", {}),
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get company {slug}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
