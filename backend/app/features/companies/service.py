"""Reads company profiles from data/companies/<slug>/profile.json."""
import json
from pathlib import Path

from app.core.config import settings


class CompanyService:
    def get_profile(self, slug: str) -> dict | None:
        path = Path(settings.companies_dir) / slug / "profile.json"
        if not path.exists():
            return None
        return json.loads(path.read_text())

    def get_logo_path(self, slug: str) -> Path | None:
        path = Path(settings.companies_dir) / slug / "logo.png"
        return path if path.exists() else None
