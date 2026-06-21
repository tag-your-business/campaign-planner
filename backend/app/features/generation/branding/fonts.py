"""Loads and caches the branding font, trying premium options before falling back."""

from functools import lru_cache

from PIL import ImageFont

# Tried in order; first one that loads wins. Add entries to the front to override.
_FONT_CANDIDATES = [
    "segoeui.ttf",  # Segoe UI Regular — clean, readable weight
    "georgia.ttf",  # Georgia — elegant serif, widely available
    "DejaVuSans.ttf",
]


@lru_cache(maxsize=32)
def font_for(size: int) -> ImageFont.FreeTypeFont:
    for name in _FONT_CANDIDATES:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    # Pillow >= 10.1: load_default returns a scalable FreeTypeFont.
    return ImageFont.load_default(size)
