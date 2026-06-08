"""Loads and provides events from data/events/<year>.json."""

import json
from pathlib import Path

from app.core.config import settings


class EventService:
    def get_events(self, year: int) -> list[dict]:
        path = Path(settings.events_dir) / f"{year}.json"
        if not path.exists():
            return []
        return json.loads(path.read_text())
