"""Pure color helpers for picking readable text colors from the background."""

from PIL import Image, ImageStat

RGB = tuple[float, float, float]
RGBA = tuple[int, int, int, int]


def average_rgb(base: Image.Image, box: tuple[int, int, int, int]) -> RGB:
    x0, y0, x1, y1 = box
    x0 = max(0, min(x0, base.width))
    x1 = max(0, min(x1, base.width))
    y0 = max(0, min(y0, base.height))
    y1 = max(0, min(y1, base.height))
    if x1 <= x0 or y1 <= y0:
        region = base
    else:
        region = base.crop((x0, y0, x1, y1))
    r, g, b = ImageStat.Stat(region.convert("RGB")).mean
    return (r, g, b)


def blend_over(fill: RGBA, background: RGB) -> RGB:
    alpha = fill[3] / 255
    return tuple(c * alpha + bg * (1 - alpha) for c, bg in zip(fill[:3], background))


def luminance(rgb: RGB) -> float:
    r, g, b = rgb
    return 0.299 * r + 0.587 * g + 0.114 * b


def contrasting_text(effective: RGB, light: RGBA, dark: RGBA, threshold: float) -> RGBA:
    return dark if luminance(effective) > threshold else light
