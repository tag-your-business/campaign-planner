"""Unit tests for BrandingService — uses real Pillow with tmp_path fixtures."""

from pathlib import Path

from app.features.generation.branding import BrandingService
from app.features.generation.branding.colors import (
    average_rgb,
    blend_over,
    contrasting_text,
    luminance,
)
from app.features.generation.branding.config import LayoutConfig
from app.features.generation.branding.elements import _resolve_text_color
from app.features.generation.branding.layout import resolve_slots
from app.features.generation.branding.service import _collect_values
from PIL import Image, ImageChops

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def create_test_image(
    path: Path, width: int = 200, height: int = 200, color=(128, 128, 128)
) -> Path:
    img = Image.new("RGBA", (width, height), color + (255,))
    img.save(str(path), "PNG")
    return path


def create_test_logo(
    path: Path, width: int = 40, height: int = 40, color=(255, 0, 0)
) -> Path:
    logo = Image.new("RGBA", (width, height), color + (200,))
    logo.save(str(path), "PNG")
    return path


def _changed_x_extent(base_path: Path, out_path: Path, rows: range) -> tuple[int, int]:
    """Horizontal span (min_x, max_x) of pixels in `rows` that differ from base."""
    base_px = Image.open(base_path).convert("RGB").load()
    out_img = Image.open(out_path).convert("RGB")
    out_px = out_img.load()
    width, _ = out_img.size
    min_x = max_x = None
    for y in rows:
        for x in range(width):
            if base_px[x, y] != out_px[x, y]:
                min_x = x if min_x is None else min(min_x, x)
                max_x = x if max_x is None else max(max_x, x)
    return min_x, max_x


# ---------------------------------------------------------------------------
# Pure-function tests (deterministic, no rendering)
# ---------------------------------------------------------------------------


class TestResolveSlots:
    def test_defaults_no_collision(self):
        assert resolve_slots("top-left", "top-right", True) == ("top-left", "top-right")

    def test_collision_moves_contact_to_opposite(self):
        assert resolve_slots("top-right", "top-right", True) == (
            "top-right",
            "top-left",
        )

    def test_no_logo_keeps_contact_preference(self):
        assert resolve_slots("top-left", "top-left", False) == ("top-left", "top-left")

    def test_invalid_positions_fall_back_to_defaults(self):
        assert resolve_slots("middle", "nowhere", True) == ("top-left", "top-right")


class TestCollectValues:
    def test_ordered_values(self):
        source = {"website": "a", "address": "b"}
        assert _collect_values(source, ["website", "address"]) == ["a", "b"]

    def test_missing_key_skipped(self):
        assert _collect_values({"website": "a"}, ["website", "phone"]) == ["a"]

    def test_blank_value_skipped(self):
        assert _collect_values({"website": "   "}, ["website"]) == []


# ---------------------------------------------------------------------------
# No-logo tests
# ---------------------------------------------------------------------------


class TestBrandingServiceNoLogo:
    def test_no_logo_returns_output_path(self, tmp_path):
        base = create_test_image(tmp_path / "base.png")
        out = tmp_path / "out.png"
        svc = BrandingService()
        result = svc.apply(base, out)
        assert result == out

    def test_no_logo_creates_output_file(self, tmp_path):
        base = create_test_image(tmp_path / "base.png")
        out = tmp_path / "out.png"
        svc = BrandingService()
        svc.apply(base, out)
        assert out.exists()

    def test_no_logo_output_is_valid_image(self, tmp_path):
        base = create_test_image(tmp_path / "base.png", width=300, height=300)
        out = tmp_path / "out.png"
        svc = BrandingService()
        svc.apply(base, out)
        img = Image.open(out)
        assert img.size == (300, 300)

    def test_empty_profile_does_not_crash(self, tmp_path):
        base = create_test_image(tmp_path / "base.png", width=400, height=400)
        out = tmp_path / "out.png"
        svc = BrandingService()
        svc.apply(base, out, {})
        img = Image.open(out)
        assert img.size == (400, 400)

    def test_missing_logo_path_falls_back_gracefully(self, tmp_path):
        base = create_test_image(tmp_path / "base.png")
        nonexistent_logo = tmp_path / "ghost_logo.png"
        out = tmp_path / "out.png"
        svc = BrandingService()
        result = svc.apply(base, out, {}, nonexistent_logo)
        assert result == out
        assert out.exists()


# ---------------------------------------------------------------------------
# With-logo tests
# ---------------------------------------------------------------------------


class TestBrandingServiceWithLogo:
    def test_with_logo_creates_output_file(self, tmp_path):
        base = create_test_image(tmp_path / "base.png")
        logo = create_test_logo(tmp_path / "logo.png")
        out = tmp_path / "out.png"
        svc = BrandingService()
        svc.apply(base, out, {}, logo)
        assert out.exists()

    def test_with_logo_preserves_base_image_dimensions(self, tmp_path):
        base = create_test_image(tmp_path / "base.png", width=512, height=512)
        logo = create_test_logo(tmp_path / "logo.png", width=100, height=50)
        out = tmp_path / "out.png"
        svc = BrandingService()
        svc.apply(base, out, {}, logo)
        img = Image.open(out)
        assert img.size == (512, 512)

    def test_with_logo_output_differs_from_no_logo(self, tmp_path):
        base = create_test_image(
            tmp_path / "base.png", width=400, height=400, color=(128, 128, 128)
        )
        logo = create_test_logo(
            tmp_path / "logo.png", width=80, height=80, color=(255, 0, 0)
        )
        out_branded = tmp_path / "branded.png"
        out_plain = tmp_path / "plain.png"
        svc = BrandingService()
        svc.apply(base, out_branded, {}, logo)
        svc.apply(base, out_plain)
        assert out_branded.read_bytes() != out_plain.read_bytes()


# ---------------------------------------------------------------------------
# Contact + banner tests
# ---------------------------------------------------------------------------


class TestBrandingServiceText:
    def test_banner_renders_at_bottom(self, tmp_path):
        base = create_test_image(tmp_path / "base.png", width=1024, height=1024)
        out = tmp_path / "out.png"
        profile = {
            "contact_info": {"website": "www.example.com"},
            "branding": {"banner_fields": ["website"]},
        }
        svc = BrandingService()
        svc.apply(base, out, profile)
        # Bottom band should contain rendered (changed) pixels.
        min_x, max_x = _changed_x_extent(base, out, range(900, 1020))
        assert min_x is not None and max_x is not None

    def test_banner_width_grows_with_text_length(self, tmp_path):
        base = create_test_image(tmp_path / "base.png", width=1024, height=1024)
        svc = BrandingService()

        short_out = tmp_path / "short.png"
        long_out = tmp_path / "long.png"
        svc.apply(
            base,
            short_out,
            {
                "contact_info": {"website": "a.co"},
                "branding": {"banner_fields": ["website"]},
            },
        )
        svc.apply(
            base,
            long_out,
            {
                "contact_info": {
                    "website": "www.a-much-longer-domain-name.example.com"
                },
                "branding": {"banner_fields": ["website"]},
            },
        )

        rows = range(900, 1020)
        smin, smax = _changed_x_extent(base, short_out, rows)
        lmin, lmax = _changed_x_extent(base, long_out, rows)
        assert (lmax - lmin) > (smax - smin)

    def test_contact_block_renders(self, tmp_path):
        base = create_test_image(tmp_path / "base.png", width=1024, height=1024)
        out_branded = tmp_path / "branded.png"
        out_plain = tmp_path / "plain.png"
        profile = {
            "contact_info": {"email": "hello@example.com"},
            "branding": {"contact_fields": ["email"], "contact_position": "top-right"},
        }
        svc = BrandingService()
        svc.apply(base, out_branded, profile)
        svc.apply(base, out_plain)
        assert out_branded.read_bytes() != out_plain.read_bytes()


# ---------------------------------------------------------------------------
# Fallback / resilience tests
# ---------------------------------------------------------------------------


class TestBrandingServiceFallback:
    def test_corrupt_logo_still_produces_image(self, tmp_path):
        base = create_test_image(tmp_path / "base.png", width=200, height=200)
        corrupt_logo = tmp_path / "bad_logo.png"
        corrupt_logo.write_bytes(b"not a valid image")
        out = tmp_path / "out.png"
        svc = BrandingService()
        result = svc.apply(base, out, {}, corrupt_logo)
        assert result == out
        assert out.exists()
        img = Image.open(out)
        assert img.size == (200, 200)

    def test_different_sized_base_images_all_succeed(self, tmp_path):
        logo = create_test_logo(tmp_path / "logo.png")
        svc = BrandingService()
        for i, (w, h) in enumerate([(100, 100), (512, 512), (1024, 1024)]):
            base = create_test_image(tmp_path / f"base_{i}.png", width=w, height=h)
            out = tmp_path / f"out_{i}.png"
            result = svc.apply(base, out, {}, logo)
            assert result == out
            img = Image.open(out)
            assert img.size == (w, h)


# ---------------------------------------------------------------------------
# Color helpers (pure functions)
# ---------------------------------------------------------------------------


class TestColorHelpers:
    def test_luminance_extremes(self):
        assert luminance((0, 0, 0)) == 0
        assert luminance((255, 255, 255)) == 255

    def test_blend_opaque_returns_fill(self):
        assert blend_over((10, 20, 30, 255), (200, 200, 200)) == (10, 20, 30)

    def test_blend_transparent_returns_background(self):
        assert blend_over((10, 20, 30, 0), (200, 200, 200)) == (200, 200, 200)

    def test_contrasting_text_picks_dark_on_bright(self):
        light, dark = (255, 255, 255, 255), (0, 0, 0, 255)
        assert contrasting_text((250, 250, 250), light, dark, 140.0) == dark

    def test_contrasting_text_picks_light_on_dim(self):
        light, dark = (255, 255, 255, 255), (0, 0, 0, 255)
        assert contrasting_text((10, 10, 10), light, dark, 140.0) == light

    def test_average_rgb_solid_image(self):
        img = Image.new("RGB", (20, 20), (120, 60, 30))
        r, g, b = average_rgb(img, (0, 0, 20, 20))
        assert (round(r), round(g), round(b)) == (120, 60, 30)

    def test_average_rgb_clamps_out_of_bounds_box(self):
        img = Image.new("RGB", (20, 20), (50, 50, 50))
        r, g, b = average_rgb(img, (-10, -10, 999, 999))
        assert (round(r), round(g), round(b)) == (50, 50, 50)


# ---------------------------------------------------------------------------
# Smart text-color selection
# ---------------------------------------------------------------------------


class TestSmartTextColor:
    def test_light_fill_flips_text_with_background(self):
        # A light, translucent fill lets the background drive the contrast pick.
        cfg = LayoutConfig(banner_color=(255, 255, 255, 128))
        white = Image.new("RGB", (40, 40), (255, 255, 255))
        black = Image.new("RGB", (40, 40), (0, 0, 0))
        box = (0, 0, 40, 40)
        assert (
            _resolve_text_color(white, box, cfg, cfg.banner_color)
            == cfg.dark_text_color
        )
        assert _resolve_text_color(black, box, cfg, cfg.banner_color) == cfg.text_color

    def test_dynamic_off_uses_static_text_color(self):
        cfg = LayoutConfig(dynamic_text_color=False)
        white = Image.new("RGB", (40, 40), (255, 255, 255))
        box = (0, 0, 40, 40)
        assert _resolve_text_color(white, box, cfg, cfg.banner_color) == cfg.text_color


# ---------------------------------------------------------------------------
# Banner shape (circular ends) + border
# ---------------------------------------------------------------------------


def _changed_bbox(base_path: Path, out_path: Path):
    base = Image.open(base_path).convert("RGB")
    out = Image.open(out_path).convert("RGB")
    return ImageChops.difference(base, out).getbbox()


class TestBannerShape:
    def _render_banner_only(self, tmp_path):
        base = create_test_image(tmp_path / "base.png", width=1024, height=1024)
        out = tmp_path / "out.png"
        profile = {
            "contact_info": {"website": "www.example.com"},
            "branding": {"banner_fields": ["website"]},
        }
        BrandingService().apply(base, out, profile)
        return base, out

    def test_banner_ends_are_circular(self, tmp_path):
        base, out = self._render_banner_only(tmp_path)
        x0, y0, x1, y1 = _changed_bbox(base, out)
        base_px = Image.open(base).convert("RGB").load()
        out_px = Image.open(out).convert("RGB").load()
        mid_y = (y0 + y1) // 2
        # The bounding-box corner is cut away by the circular end (unchanged)...
        assert out_px[x0, y0] == base_px[x0, y0]
        # ...while the left tip at vertical center is filled (changed).
        assert out_px[x0, mid_y] != base_px[x0, mid_y]

    def test_banner_has_border_in_text_color(self, tmp_path):
        base, out = self._render_banner_only(tmp_path)
        x0, y0, x1, y1 = _changed_bbox(base, out)
        out_px = Image.open(out).convert("RGB").load()
        # The top edge of the pill is the border, drawn in the (white) text color.
        found = any(out_px[x, y0] == (255, 255, 255) for x in range(x0, x1))
        assert found


# ---------------------------------------------------------------------------
# PNG logo transparency
# ---------------------------------------------------------------------------


class TestLogoPngTransparency:
    def test_transparent_logo_region_leaves_base_untouched(self, tmp_path):
        base = create_test_image(tmp_path / "base.png", width=1024, height=1024)
        # Logo: left half fully transparent, right half opaque red.
        logo_img = Image.new("RGBA", (100, 100), (0, 0, 0, 0))
        for x in range(50, 100):
            for y in range(100):
                logo_img.putpixel((x, y), (255, 0, 0, 255))
        logo = tmp_path / "logo.png"
        logo_img.save(logo, "PNG")

        out = tmp_path / "out.png"
        profile = {"branding": {"logo_position": "top-left"}}
        BrandingService().apply(base, out, profile, logo)

        base_px = Image.open(base).convert("RGB").load()
        out_px = Image.open(out).convert("RGB").load()
        margin = round(0.03 * 1024)
        # A pixel in the transparent (left) half of the placed logo == base.
        assert out_px[margin + 5, margin + 50] == base_px[margin + 5, margin + 50]
        # A pixel in the opaque (right) half differs from base.
        assert out_px[margin + 90, margin + 50] != base_px[margin + 90, margin + 50]
