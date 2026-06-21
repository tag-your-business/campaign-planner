"""Overlays company branding (logo, contact block, bottom banner) onto images."""

import logging
from pathlib import Path

from app.features.generation.branding.config import LayoutConfig
from app.features.generation.branding.elements import (
    render_banner,
    render_contact_block,
    render_logo,
)
from app.features.generation.branding.layout import resolve_slots
from PIL import Image

logger = logging.getLogger(__name__)

DEFAULT_LOGO_POSITION = "top-left"
DEFAULT_CONTACT_POSITION = "top-right"


class BrandingService:
    """Applies company branding to generated images using a slot-based layout."""

    def apply(
        self,
        image_path: Path,
        output_path: Path,
        profile: dict | None = None,
        logo_path: Path | None = None,
    ) -> Path:
        try:
            base = Image.open(image_path).convert("RGBA")
            overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
            cfg = LayoutConfig()

            profile = profile or {}
            branding = profile.get("branding") or {}
            contact_info = profile.get("contact_info") or {}

            has_logo = logo_path is not None and Path(logo_path).exists()
            if logo_path is not None and not has_logo:
                logger.warning(f"Logo not found at {logo_path}, continuing without it")
            logo_slot, contact_slot = resolve_slots(
                branding.get("logo_position", DEFAULT_LOGO_POSITION),
                branding.get("contact_position", DEFAULT_CONTACT_POSITION),
                has_logo,
            )

            if has_logo:
                try:
                    logo_img = Image.open(logo_path).convert("RGBA")
                    render_logo(overlay, logo_img, logo_slot, cfg)
                except Exception as logo_error:
                    logger.warning(f"Failed to render logo: {logo_error}")

            contact_lines = _collect_values(
                contact_info, branding.get("contact_fields", [])
            )
            if contact_lines:
                render_contact_block(overlay, base, contact_lines, contact_slot, cfg)

            banner_values = _collect_values(
                contact_info, branding.get("banner_fields", [])
            )
            if banner_values:
                render_banner(overlay, base, " | ".join(banner_values), cfg)

            result = Image.alpha_composite(base, overlay).convert("RGB")
            result.save(output_path, "PNG")
            logger.info(f"Applied branding to image: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to apply branding: {e}")
            return _save_unbranded(image_path, output_path)


def _collect_values(source: dict, keys: list[str]) -> list[str]:
    values = []
    for key in keys:
        value = str(source.get(key, "")).strip()
        if value:
            values.append(value)
    return values


def _save_unbranded(image_path: Path, output_path: Path) -> Path:
    try:
        Image.open(image_path).convert("RGB").save(output_path, "PNG")
        logger.warning("Saved image without branding due to error")
    except Exception as fallback_error:
        logger.error(f"Failed to save fallback image: {fallback_error}")
        raise
    return output_path
