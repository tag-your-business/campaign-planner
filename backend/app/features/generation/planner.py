"""Decides which campaigns to generate for a company + event combination."""

import logging
from datetime import datetime, timedelta
from typing import Optional

from app.core.config import settings

logger = logging.getLogger(__name__)


class CampaignPlanner:
    """Plans campaigns by matching events to companies based on industry relevance."""

    # Industry-specific event keywords
    INDUSTRY_EVENT_MAPPING = {
        "dental": ["oral", "teeth", "dental", "smile", "health"],
        "healthcare": ["health", "wellness", "medical", "care", "awareness"],
        "restaurant": ["food", "culinary", "dining", "taste"],
        "retail": ["shopping", "sale", "retail", "consumer"],
        "fitness": ["fitness", "health", "wellness", "active", "exercise"],
        "beauty": ["beauty", "skincare", "wellness", "spa"],
    }

    # Universal events that apply to all industries
    UNIVERSAL_TAGS = ["holiday", "seasonal", "celebration"]

    def plan(self, company_profile: dict, event: dict) -> Optional[dict]:
        """
        Create a campaign spec if the event is relevant to the company.

        Args:
            company_profile: Company profile dictionary with industry, tone, etc.
            event: Event dictionary with name, date, tags, etc.

        Returns:
            Campaign specification dict if relevant, None otherwise
        """
        # Check if event is relevant to this company
        if not self._is_event_relevant(company_profile, event):
            logger.debug(
                f"Event {event.get('name')} not relevant for "
                f"{company_profile.get('name')} ({company_profile.get('industry')})"
            )
            return None

        # Calculate dates
        event_date = datetime.fromisoformat(event.get("date"))
        scheduled_publish_date = event_date - timedelta(days=settings.publish_lead_days)

        # Build campaign specification
        campaign_spec = {
            # Company info
            "company_slug": company_profile.get("slug"),
            "company_name": company_profile.get("name"),
            "industry": company_profile.get("industry"),
            "tone": company_profile.get("tone"),
            "brand_colors": company_profile.get("brand_colors", []),
            # Event info
            "event_id": event.get("id"),
            "event_name": event.get("name"),
            "event_date": event.get("date"),
            "event_tags": event.get("tags", []),
            # Publishing info
            "platforms": ["facebook", "instagram"],
            "scheduled_publish_date": scheduled_publish_date.isoformat(),
            # Social media IDs
            "facebook_page_id": company_profile.get("social", {}).get(
                "facebook_page_id", ""
            ),
            "instagram_account_id": company_profile.get("social", {}).get(
                "instagram_account_id", ""
            ),
        }

        logger.info(
            f"Planned campaign: {company_profile.get('name')} - {event.get('name')}"
        )

        return campaign_spec

    def _is_event_relevant(self, company_profile: dict, event: dict) -> bool:
        """
        Determine if an event is relevant to a company.

        Universal holidays apply to all companies.
        Industry-specific events only apply to matching industries.
        """
        event_tags = event.get("tags", [])
        event_name = event.get("name", "").lower()
        event_id = event.get("id", "").lower()
        company_industry = company_profile.get("industry", "").lower()

        # Check if it's a universal event
        if any(tag in self.UNIVERSAL_TAGS for tag in event_tags):
            return True

        # Check for industry-specific relevance
        industry_keywords = self.INDUSTRY_EVENT_MAPPING.get(company_industry, [])

        # Check if any industry keyword appears in event name or ID
        for keyword in industry_keywords:
            if keyword in event_name or keyword in event_id:
                return True

        # Not relevant
        return False
