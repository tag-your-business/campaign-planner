"""All tunable visual constants for branding, as fractions of the image width."""

from dataclasses import dataclass


@dataclass(frozen=True)
class LayoutConfig:
    """Visual constants for the branding overlay (fractions of image width)."""

    # Spacing / sizing (fractions of image width)
    margin_frac: float = 0.03
    logo_width_frac: float = 0.10
    contact_font_frac: float = 0.022
    banner_font_frac: float = 0.024
    h_pad_frac: float = 0.028  # horizontal padding (left/right inside pill)
    v_pad_top_frac: float = 0.013  # vertical padding — top
    v_pad_bot_frac: float = 0.018  # vertical padding — bottom (slightly more)
    line_spacing_frac: float = 0.006
    corner_radius_frac: float = 0.010
    banner_margin_frac: float = 0.025
    banner_border_frac: float = 0.003

    # Colors (RGBA)
    scrim_color: tuple[int, int, int, int] = (0, 0, 0, 115)
    banner_color: tuple[int, int, int, int] = (0, 0, 0, 140)
    text_color: tuple[int, int, int, int] = (255, 255, 255, 255)
    dark_text_color: tuple[int, int, int, int] = (0, 0, 0, 255)

    # Pick text/border color from the background for contrast (no AI).
    dynamic_text_color: bool = True
    contrast_threshold: float = 140.0

    def px(self, frac: float, width: int) -> int:
        return max(1, round(frac * width))
