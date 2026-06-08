"""Overlays company branding (logo, colors) onto a generated image."""

from pathlib import Path


class BrandingService:
    def apply(
        self, image_path: Path, logo_path: Path | None, output_path: Path
    ) -> Path:
        raise NotImplementedError
