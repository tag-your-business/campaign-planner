"""Persists campaign artifacts and metadata to the filesystem."""
import json
from pathlib import Path

from app.core.config import settings


class StorageService:
    def save_metadata(self, campaign_id: str, metadata: dict) -> Path:
        path = Path(settings.campaigns_dir) / "generated" / campaign_id / "metadata.json"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(metadata, indent=2))
        return path

    def get_pending(self) -> list[dict]:
        base = Path(settings.campaigns_dir) / "generated"
        pending = []
        for meta_file in base.glob("*/metadata.json"):
            data = json.loads(meta_file.read_text())
            if data.get("status") == "pending":
                pending.append(data)
        return pending

    def update_status(self, campaign_id: str, status: str) -> None:
        path = Path(settings.campaigns_dir) / "generated" / campaign_id / "metadata.json"
        data = json.loads(path.read_text())
        data["status"] = status
        path.write_text(json.dumps(data, indent=2))
