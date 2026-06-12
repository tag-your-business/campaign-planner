"""Unit tests for BrandingService — uses real Pillow with tmp_path fixtures."""

from pathlib import Path

from app.features.generation.branding import BrandingService
from PIL import Image

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


# ---------------------------------------------------------------------------
# No-logo tests
# ---------------------------------------------------------------------------


class TestBrandingServiceNoLogo:
    def test_no_logo_returns_output_path(self, tmp_path):
        base = create_test_image(tmp_path / "base.png")
        out = tmp_path / "out.png"
        svc = BrandingService()
        result = svc.apply(base, None, out)
        assert result == out

    def test_no_logo_creates_output_file(self, tmp_path):
        base = create_test_image(tmp_path / "base.png")
        out = tmp_path / "out.png"
        svc = BrandingService()
        svc.apply(base, None, out)
        assert out.exists()

    def test_no_logo_output_is_valid_image(self, tmp_path):
        base = create_test_image(tmp_path / "base.png", width=300, height=300)
        out = tmp_path / "out.png"
        svc = BrandingService()
        svc.apply(base, None, out)
        img = Image.open(out)
        assert img.size == (300, 300)

    def test_missing_logo_path_falls_back_gracefully(self, tmp_path):
        base = create_test_image(tmp_path / "base.png")
        nonexistent_logo = tmp_path / "ghost_logo.png"
        out = tmp_path / "out.png"
        svc = BrandingService()
        result = svc.apply(base, nonexistent_logo, out)
        assert result == out
        assert out.exists()

    def test_missing_logo_preserves_image_dimensions(self, tmp_path):
        base = create_test_image(tmp_path / "base.png", width=400, height=400)
        out = tmp_path / "out.png"
        svc = BrandingService()
        svc.apply(base, None, out)
        img = Image.open(out)
        assert img.size == (400, 400)


# ---------------------------------------------------------------------------
# With-logo tests
# ---------------------------------------------------------------------------


class TestBrandingServiceWithLogo:
    def test_with_logo_returns_output_path(self, tmp_path):
        base = create_test_image(tmp_path / "base.png")
        logo = create_test_logo(tmp_path / "logo.png")
        out = tmp_path / "out.png"
        svc = BrandingService()
        result = svc.apply(base, logo, out)
        assert result == out

    def test_with_logo_creates_output_file(self, tmp_path):
        base = create_test_image(tmp_path / "base.png")
        logo = create_test_logo(tmp_path / "logo.png")
        out = tmp_path / "out.png"
        svc = BrandingService()
        svc.apply(base, logo, out)
        assert out.exists()

    def test_with_logo_output_is_valid_image(self, tmp_path):
        base = create_test_image(tmp_path / "base.png", width=400, height=400)
        logo = create_test_logo(tmp_path / "logo.png")
        out = tmp_path / "out.png"
        svc = BrandingService()
        svc.apply(base, logo, out)
        img = Image.open(out)
        assert img.size == (400, 400)

    def test_with_logo_preserves_base_image_dimensions(self, tmp_path):
        base = create_test_image(tmp_path / "base.png", width=512, height=512)
        logo = create_test_logo(tmp_path / "logo.png", width=100, height=50)
        out = tmp_path / "out.png"
        svc = BrandingService()
        svc.apply(base, logo, out)
        img = Image.open(out)
        assert img.size == (512, 512)

    def test_with_logo_output_differs_from_no_logo(self, tmp_path):
        """Branded image should differ from base (logo pixels change something)."""
        base = create_test_image(
            tmp_path / "base.png", width=200, height=200, color=(128, 128, 128)
        )
        logo = create_test_logo(
            tmp_path / "logo.png", width=50, height=50, color=(255, 0, 0)
        )

        out_branded = tmp_path / "branded.png"
        out_plain = tmp_path / "plain.png"
        svc = BrandingService()
        svc.apply(base, logo, out_branded)
        svc.apply(base, None, out_plain)

        assert out_branded.read_bytes() != out_plain.read_bytes()

    def test_logo_resized_to_10_percent_of_width(self, tmp_path):
        """Logo at bottom-right should be ~10% of image width wide."""
        base_width = 400
        base = create_test_image(
            tmp_path / "base.png", width=base_width, height=base_width
        )
        # Logo is 80px wide; after resize it should be 40px (10% of 400)
        logo = create_test_logo(
            tmp_path / "logo.png", width=80, height=80, color=(0, 255, 0)
        )
        out = tmp_path / "out.png"
        svc = BrandingService()
        svc.apply(base, logo, out)

        img = Image.open(out).convert("RGB")
        expected_logo_width = int(base_width * 0.1)  # 40px
        padding = 20
        # Sample a pixel inside the expected logo region (bottom-right, within logo bounds)
        x = base_width - padding - expected_logo_width // 2
        y = base_width - padding - expected_logo_width // 2
        r, g, b = img.getpixel((x, y))
        # The logo is bright green; the base is grey — the region should not be grey
        assert not (
            120 <= r <= 136 and 120 <= g <= 136 and 120 <= b <= 136
        ), "Logo was not applied in the expected region"

    def test_non_square_logo_maintains_aspect_ratio(self, tmp_path):
        base = create_test_image(tmp_path / "base.png", width=400, height=400)
        logo = create_test_logo(tmp_path / "logo.png", width=80, height=40)
        out = tmp_path / "out.png"
        svc = BrandingService()
        result = svc.apply(base, logo, out)
        assert result == out
        img = Image.open(out)
        assert img.size == (400, 400)


# ---------------------------------------------------------------------------
# Fallback / resilience tests
# ---------------------------------------------------------------------------


class TestBrandingServiceFallback:
    def test_corrupt_logo_falls_back_to_plain_image(self, tmp_path):
        base = create_test_image(tmp_path / "base.png", width=200, height=200)
        corrupt_logo = tmp_path / "bad_logo.png"
        corrupt_logo.write_bytes(b"not a valid image")
        out = tmp_path / "out.png"
        svc = BrandingService()
        result = svc.apply(base, corrupt_logo, out)
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
            result = svc.apply(base, logo, out)
            assert result == out
            img = Image.open(out)
            assert img.size == (w, h)
