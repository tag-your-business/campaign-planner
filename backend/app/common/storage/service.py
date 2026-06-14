"""Persists campaign artifacts and metadata to the filesystem."""

import json
from datetime import datetime
from pathlib import Path

from app.core.config import settings


class StorageService:
    def save_metadata(self, campaign_id: str, metadata: dict) -> Path:
        path = (
            Path(settings.campaigns_dir) / "generated" / campaign_id / "metadata.json"
        )
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
        path = (
            Path(settings.campaigns_dir) / "generated" / campaign_id / "metadata.json"
        )
        data = json.loads(path.read_text())
        data["status"] = status
        path.write_text(json.dumps(data, indent=2))

    def update_platform_status(
        self, campaign_id: str, platform: str, status: str, post_id: str | None = None
    ) -> None:
        path = (
            Path(settings.campaigns_dir) / "generated" / campaign_id / "metadata.json"
        )
        data = json.loads(path.read_text())

        # Initialize platform_statuses if it doesn't exist
        if "platform_statuses" not in data:
            data["platform_statuses"] = {}

        # Update platform-specific status
        data["platform_statuses"][platform] = {
            "status": status,
            "post_id": post_id,
            "published_at": (
                datetime.now().isoformat() if status == "published" else None
            ),
        }

        # Recalculate overall status based on all platforms
        data["status"] = self._calculate_overall_status(data)

        path.write_text(json.dumps(data, indent=2))

    def _calculate_overall_status(self, metadata: dict) -> str:
        platform_statuses = metadata.get("platform_statuses", {})
        platforms = metadata.get("platforms", [])

        # If no platforms configured, use existing status
        if not platforms:
            return metadata.get("status", "pending")

        # Get all platform statuses
        statuses = []
        for platform in platforms:
            platform_status = platform_statuses.get(platform, {}).get(
                "status", "pending"
            )
            statuses.append(platform_status)

        # Check if any platform failed
        if "failed" in statuses:
            return "failed"

        # Check if all platforms published
        if all(status == "published" for status in statuses):
            return "published"

        # Otherwise, still pending
        return "pending"

    def update_image_url(self, campaign_id: str, image_url: str) -> None:
        path = (
            Path(settings.campaigns_dir) / "generated" / campaign_id / "metadata.json"
        )
        data = json.loads(path.read_text())
        data["image_url"] = image_url
        path.write_text(json.dumps(data, indent=2))
