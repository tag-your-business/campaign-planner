"""
Script to generate sample E2E test data.

Creates a sample campaign with metadata and a test image for E2E testing.
Run this script to set up the required test data before running E2E tests.

Usage:
    python tests/e2e/generate_sample_data.py
"""

import json
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


def create_test_image(output_path: Path) -> None:
    """
    Create a 1080x1080 test image with Facebook blue background.

    Args:
        output_path: Path where the image should be saved
    """
    # Facebook blue color
    fb_blue = (66, 103, 178)

    # Create image
    img = Image.new("RGB", (1080, 1080), fb_blue)
    draw = ImageDraw.Draw(img)

    # Try to use a default font, fallback to PIL default if not available
    try:
        # Try to use a system font (this works on most systems)
        font_large = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 80)
        font_small = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 40)
    except (OSError, IOError):
        # Fallback to default PIL font
        font_large = ImageFont.load_default()
        font_small = ImageFont.load_default()

    # Draw text
    text_main = "E2E TEST"
    text_sub = "Safe to Delete"

    # Get text bounding boxes for centering
    bbox_main = draw.textbbox((0, 0), text_main, font=font_large)
    bbox_sub = draw.textbbox((0, 0), text_sub, font=font_small)

    # Calculate positions to center text
    x_main = (1080 - (bbox_main[2] - bbox_main[0])) // 2
    y_main = (1080 - (bbox_main[3] - bbox_main[1])) // 2 - 50

    x_sub = (1080 - (bbox_sub[2] - bbox_sub[0])) // 2
    y_sub = y_main + 100

    # Draw white text
    draw.text((x_main, y_main), text_main, fill=(255, 255, 255), font=font_large)
    draw.text((x_sub, y_sub), text_sub, fill=(255, 255, 255), font=font_small)

    # Save image
    img.save(output_path, "JPEG", quality=95)
    print(f"✅ Created test image: {output_path}")


def create_metadata(output_path: Path) -> None:
    """
    Create sample campaign metadata.json.

    Args:
        output_path: Path where the metadata should be saved
    """
    metadata = {
        "id": "sample-e2e-campaign",
        "company_name": "E2E Test Company",
        "event_name": "E2E Test Event",
        "status": "pending",
        "platforms": ["facebook", "instagram"],
        "platform_statuses": {
            "facebook": {"status": "pending", "post_id": None, "published_at": None},
            "instagram": {"status": "pending", "post_id": None, "published_at": None},
        },
        "facebook_page_id": "PLACEHOLDER_UPDATE_IN_FIXTURE",
        "instagram_account_id": "PLACEHOLDER_UPDATE_IN_FIXTURE",
        "caption": "🧪 This is an E2E test post. You can safely delete this after testing.",
        "image_path": "PLACEHOLDER_UPDATE_IN_FIXTURE",
        "image_url": "PLACEHOLDER_UPDATE_IN_FIXTURE",
        "generated_at": datetime.now().isoformat(),
        "scheduled_publish_date": datetime.now().strftime("%Y-%m-%d"),
    }

    with open(output_path, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"✅ Created metadata: {output_path}")


def main() -> None:
    """Generate all sample E2E test data."""
    # Determine the base directory (tests/e2e/)
    script_dir = Path(__file__).parent
    data_dir = script_dir / "data" / "campaigns" / "generated" / "sample-e2e-campaign"

    # Create directory if it doesn't exist
    data_dir.mkdir(parents=True, exist_ok=True)
    print(f"📁 Using data directory: {data_dir}")

    # Create test image
    image_path = data_dir / "image.jpg"
    create_test_image(image_path)

    # Create metadata
    metadata_path = data_dir / "metadata.json"
    create_metadata(metadata_path)

    print("\n✨ Sample E2E data generation complete!")
    print("\nNext steps:")
    print("1. Copy tests/e2e/.env.e2e.example to tests/e2e/.env.e2e")
    print("2. Update the credentials in .env.e2e")
    print("3. Run: poetry run pytest tests/e2e/ -m e2e -v")


if __name__ == "__main__":
    main()
