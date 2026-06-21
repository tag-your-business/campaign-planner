"""Measure-and-render components for each branding element."""

from app.features.generation.branding.colors import (
    average_rgb,
    blend_over,
    contrasting_text,
)
from app.features.generation.branding.config import LayoutConfig
from app.features.generation.branding.fonts import font_for
from app.features.generation.branding.layout import TOP_RIGHT, corner_origin
from PIL import Image, ImageDraw, ImageFont


def _text_size(
    draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont
) -> tuple[int, int]:
    left, top, right, bottom = draw.textbbox((0, 0), text, font=font)
    return right - left, bottom - top


def _resolve_text_color(
    base: Image.Image,
    box: tuple[int, int, int, int],
    cfg: LayoutConfig,
    fill: tuple[int, int, int, int],
) -> tuple[int, int, int, int]:
    if not cfg.dynamic_text_color:
        return cfg.text_color
    effective = blend_over(fill, average_rgb(base, box))
    return contrasting_text(
        effective, cfg.text_color, cfg.dark_text_color, cfg.contrast_threshold
    )


def render_logo(
    overlay: Image.Image, logo_img: Image.Image, slot: str, cfg: LayoutConfig
) -> None:
    width = overlay.width
    target_w = cfg.px(cfg.logo_width_frac, width)
    aspect = logo_img.height / logo_img.width
    target_h = max(1, round(target_w * aspect))
    resized = logo_img.resize((target_w, target_h), Image.Resampling.LANCZOS)
    margin = cfg.px(cfg.margin_frac, width)
    x, y = corner_origin(
        slot, target_w, target_h, overlay.width, overlay.height, margin
    )
    overlay.paste(resized, (x, y), resized)


def render_contact_block(
    overlay: Image.Image,
    base: Image.Image,
    lines: list[str],
    slot: str,
    cfg: LayoutConfig,
) -> None:
    draw = ImageDraw.Draw(overlay)
    width = overlay.width
    font = font_for(cfg.px(cfg.contact_font_frac, width))
    h_pad = cfg.px(cfg.h_pad_frac, width)
    v_top = cfg.px(cfg.v_pad_top_frac, width)
    v_bot = cfg.px(cfg.v_pad_bot_frac, width)
    spacing = cfg.px(cfg.line_spacing_frac, width)

    sizes = [_text_size(draw, line, font) for line in lines]
    text_w = max(tw for tw, _ in sizes)
    line_h = max(th for _, th in sizes)
    block_w = text_w + 2 * h_pad
    block_h = len(lines) * line_h + (len(lines) - 1) * spacing + v_top + v_bot

    margin = cfg.px(cfg.margin_frac, width)
    x, y = corner_origin(slot, block_w, block_h, overlay.width, overlay.height, margin)
    box = (x, y, x + block_w, y + block_h)
    text_color = _resolve_text_color(base, box, cfg, cfg.scrim_color)
    border_w = cfg.px(cfg.banner_border_frac, width)
    # Pill shape: radius = half the height gives semicircular ends.
    radius = block_h // 2
    draw.rounded_rectangle(
        list(box),
        radius=radius,
        fill=cfg.scrim_color,
        outline=text_color,
        width=border_w,
    )

    right_align = slot == TOP_RIGHT
    text_y = y + v_top
    for (tw, _), line in zip(sizes, lines):
        text_x = x + block_w - h_pad - tw if right_align else x + h_pad
        draw.text((text_x, text_y), line, font=font, fill=text_color)
        text_y += line_h + spacing


def render_banner(
    overlay: Image.Image, base: Image.Image, text: str, cfg: LayoutConfig
) -> None:
    draw = ImageDraw.Draw(overlay)
    width, height = overlay.width, overlay.height
    font = font_for(cfg.px(cfg.banner_font_frac, width))
    h_pad = cfg.px(cfg.h_pad_frac, width)
    v_top = cfg.px(cfg.v_pad_top_frac, width)
    v_bot = cfg.px(cfg.v_pad_bot_frac, width)
    margin = cfg.px(cfg.margin_frac, width)
    text_w, text_h = _text_size(draw, text, font)
    strip_w = min(text_w + 2 * h_pad, width - 2 * margin)
    strip_h = text_h + v_top + v_bot

    bottom_margin = cfg.px(cfg.banner_margin_frac, width)
    x0 = (width - strip_w) // 2
    y1 = height - bottom_margin
    y0 = y1 - strip_h
    # Pill ends: radius = half height gives semicircular left/right ends.
    radius = strip_h // 2

    box = (x0, y0, x0 + strip_w, y1)
    text_color = _resolve_text_color(base, box, cfg, cfg.banner_color)
    border_w = cfg.px(cfg.banner_border_frac, width)
    draw.rounded_rectangle(
        list(box),
        radius=radius,
        fill=cfg.banner_color,
        outline=text_color,
        width=border_w,
    )

    text_x = x0 + (strip_w - text_w) // 2
    text_y = y0 + v_top
    draw.text((text_x, text_y), text, font=font, fill=text_color)
