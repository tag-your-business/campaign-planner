#!/usr/bin/env python3
"""
Script to run the generator flow and keep the generated files for verification.
This demonstrates the happy path test without cleanup.
"""

import json
import sys
from datetime import datetime, timedelta
from io import BytesIO
from pathlib import Path

from PIL import Image

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from unittest.mock import Mock, patch

from app.features.generation.branding import BrandingService
from app.features.generation.caption import CaptionGenerator
from app.features.generation.image import ImageService
from app.features.generation.planner import CampaignPlanner
from app.features.generation.prompt import PromptGenerator
from tests.mocks.mock_openai_client import MockOpenAIClient


def create_gradient_image():
    """Create a mock DALL-E generated image."""
    img = Image.new("RGB", (1024, 1024))
    pixels = img.load()
    for x in range(1024):
        for y in range(1024):
            red = int((x / 1024) * 255)
            green = int((y / 1024) * 255)
            blue = 128
            pixels[x, y] = (red, green, blue)
    return img


def main():
    print("=" * 70)
    print("GENERATOR FLOW - HAPPY PATH DEMONSTRATION")
    print("=" * 70)

    # Setup test data
    sample_company_dental = {
        "slug": "test_dental",
        "name": "Test Dental Practice",
        "industry": "dental",
        "tone": "professional",
        "brand_colors": ["#0066cc", "#ffffff"],
        "facebook_page_id": "dental_fb_123",
        "instagram_account_id": "dental_ig_456",
        "active": True,
    }

    event_date = (datetime.now() + timedelta(days=10)).date()
    sample_event_valentines = {
        "name": "Valentine's Day",
        "date": event_date.isoformat(),
        "tags": ["holiday", "seasonal"],
        "description": "Day of love and romance",
    }

    # Setup mock OpenAI client
    caption = (
        "Love is in the air! Book your Valentine's appointment today. 💕 "
        "#ValentinesDay #DentalCare #HealthySmile"
    )
    mock_openai = MockOpenAIClient(
        custom_caption=caption,
        custom_image_url="https://mock-openai.com/valentine-image.png",
    )

    # Mock the image download
    mock_image = create_gradient_image()
    mock_image_bytes = BytesIO()
    mock_image.save(mock_image_bytes, format="PNG")
    mock_image_bytes.seek(0)

    mock_response = Mock()
    mock_response.content = mock_image_bytes.read()
    mock_response.raise_for_status = Mock()

    # Setup paths
    base_dir = Path(__file__).parent / "tests" / "integration" / "data"
    campaigns_dir = base_dir / "campaigns" / "generated"
    event_name = sample_event_valentines["name"].lower().replace(" ", "-")
    campaign_id = f"{sample_company_dental['slug']}-{event_name}"
    campaign_dir = campaigns_dir / campaign_id
    campaign_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n📁 Campaign Directory: {campaign_dir}")
    print(f"📋 Campaign ID: {campaign_id}\n")

    # Patch OpenAI and httpx
    with patch(
        "app.features.generation.caption.OpenAI", return_value=mock_openai
    ), patch("app.features.generation.image.OpenAI", return_value=mock_openai), patch(
        "httpx.get", return_value=mock_response
    ):

        # Step 1: Plan Campaign
        print("STEP 1: Campaign Planning")
        print("-" * 70)
        planner = CampaignPlanner()
        campaign_spec = planner.plan(sample_company_dental, sample_event_valentines)
        company_name = campaign_spec["company_name"]
        event_name = campaign_spec["event_name"]
        print(f"✓ Campaign planned for: {company_name} - {event_name}")
        print(f"  Industry: {campaign_spec['industry']}")
        print(f"  Tone: {campaign_spec['tone']}")

        # Step 2: Generate Caption
        print("\nSTEP 2: Caption Generation")
        print("-" * 70)
        caption_gen = CaptionGenerator()
        caption = caption_gen.generate(campaign_spec)
        print(f"✓ Caption generated: {caption}")

        # Step 3: Generate Image Prompt
        print("\nSTEP 3: Image Prompt Generation")
        print("-" * 70)
        prompt_gen = PromptGenerator()
        image_prompt = prompt_gen.generate(campaign_spec)
        print(f"✓ Image prompt: {image_prompt[:100]}...")

        # Step 4: Generate Image
        print("\nSTEP 4: Image Generation (DALL-E)")
        print("-" * 70)
        image_service = ImageService()
        raw_image_path = campaign_dir / "image_raw.png"
        image_service.generate(image_prompt, raw_image_path)
        print(f"✓ Raw image saved: {raw_image_path}")
        print(f"  Size: {raw_image_path.stat().st_size:,} bytes")

        # Step 5: Apply Branding
        print("\nSTEP 5: Branding (Logo Overlay)")
        print("-" * 70)
        branding_service = BrandingService()
        logo_path = base_dir / "companies" / sample_company_dental["slug"] / "logo.png"
        final_image_path = campaign_dir / "image.png"
        branding_service.apply(raw_image_path, logo_path, final_image_path)
        print(f"✓ Branded image saved: {final_image_path}")
        print(f"  Size: {final_image_path.stat().st_size:,} bytes")

        # Step 6: Save Metadata
        print("\nSTEP 6: Save Campaign Metadata")
        print("-" * 70)

        # Save caption
        caption_path = campaign_dir / "caption.txt"
        with open(caption_path, "w") as f:
            f.write(caption)
        print(f"✓ Caption saved: {caption_path}")

        # Save metadata
        metadata = {
            "id": campaign_id,
            "company_slug": sample_company_dental["slug"],
            "company_name": sample_company_dental["name"],
            "event_name": sample_event_valentines["name"],
            "event_date": sample_event_valentines["date"],
            "status": "pending",
            "platforms": ["facebook", "instagram"],
            "facebook_page_id": sample_company_dental.get("facebook_page_id"),
            "instagram_account_id": sample_company_dental.get("instagram_account_id"),
            "caption": caption,
            "image_path": str(final_image_path),
            "image_url": mock_openai.custom_image_url,
            "generated_at": datetime.now().isoformat(),
            "scheduled_publish_date": sample_event_valentines["date"],
        }

        metadata_path = campaign_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)
        print(f"✓ Metadata saved: {metadata_path}")

    # Summary
    print("\n" + "=" * 70)
    print("✅ GENERATION COMPLETE!")
    print("=" * 70)
    print("\n📍 VERIFY THE GENERATED FILES AT:")
    print(f"   {campaign_dir}")
    print("\n📂 Expected Files:")
    print("   1. image_raw.png      - Raw DALL-E generated image")
    print("   2. image.png          - Branded image with logo overlay")
    print("   3. caption.txt        - Generated social media caption")
    print("   4. metadata.json      - Complete campaign metadata")

    # List actual files
    print("\n📋 Actual Files Created:")
    for file in sorted(campaign_dir.iterdir()):
        size = file.stat().st_size if file.is_file() else 0
        print(f"   ✓ {file.name:<20} ({size:,} bytes)")

    print("\n" + "=" * 70)


if __name__ == "__main__":
    main()
