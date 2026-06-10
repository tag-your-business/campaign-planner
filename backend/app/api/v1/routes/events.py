"""API endpoints for event management."""

import json
import logging
from pathlib import Path

from app.core.config import settings
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/events", tags=["events"])


class Event(BaseModel):
    """Event model."""

    id: str
    name: str
    date: str
    tags: list[str]


@router.get("/{year}", response_model=list[Event])
def get_events(year: int):
    """
    Get all events for a specific year.

    Returns a list of events with their ID, name, date, and tags.
    """
    try:
        events_path = Path(settings.events_dir) / f"{year}.json"

        if not events_path.exists():
            raise HTTPException(
                status_code=404, detail=f"Events file for year {year} not found"
            )

        events = json.loads(events_path.read_text())

        return [
            Event(
                id=e.get("id", ""),
                name=e.get("name", ""),
                date=e.get("date", ""),
                tags=e.get("tags", []),
            )
            for e in events
        ]
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get events for year {year}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
