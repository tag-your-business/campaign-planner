import json
import shutil
from datetime import datetime, timedelta
from pathlib import Path

import pytest
from PIL import Image, ImageDraw


@pytest.fixture
def temp_data_dir(monkeypatch):
    """Use integration test data directory as base for all tests."""
    # Use the integration/data directory
    data_dir = Path(__file__).parent / "integration" / "data"
    campaigns_dir = data_dir / "campaigns"

    # Clean up before test
    generated_dir = campaigns_dir / "generated"
    if generated_dir.exists():
        for item in generated_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()

    generated_dir.mkdir(parents=True, exist_ok=True)

    # Patch settings to use temp campaigns directory
    monkeypatch.setattr("app.core.config.settings.campaigns_dir", str(campaigns_dir))

    yield data_dir

    # Clean up after test
    if generated_dir.exists():
        for item in generated_dir.iterdir():
            if item.is_dir():
                shutil.rmtree(item)
            else:
                item.unlink()


@pytest.fixture
def sample_image():
    """Create a sample test image (1080x1080 blue square)."""
    img = Image.new("RGB", (1080, 1080), color="blue")

    # Save to integration/data directory
    data_dir = Path(__file__).parent / "integration" / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    img_path = data_dir / "test_image.jpg"
    img.save(img_path, "JPEG")

    yield img_path

    # Clean up after test
    if img_path.exists():
        img_path.unlink()


@pytest.fixture
def sample_campaign_facebook(sample_image, temp_data_dir):
    """Sample Facebook campaign with metadata."""
    campaign_id = "test-fb-001"
    campaign_dir = temp_data_dir / "campaigns" / "generated" / campaign_id
    campaign_dir.mkdir(parents=True)

    # Copy image to campaign directory
    campaign_image = campaign_dir / "image.jpg"
    shutil.copy(sample_image, campaign_image)

    metadata = {
        "id": campaign_id,
        "company_name": "Test Company FB",
        "event_name": "Test Event",
        "status": "pending",
        "platforms": ["facebook"],
        "facebook_page_id": "123456789",
        "caption": "Test Facebook post from integration test",
        "image_path": str(campaign_image),
        "generated_at": "2026-06-10T10:00:00Z",
        "scheduled_publish_date": "2026-06-10",
    }

    # Save metadata
    metadata_path = campaign_dir / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return metadata


@pytest.fixture
def sample_campaign_instagram(sample_image, temp_data_dir):
    """Sample Instagram campaign with metadata."""
    campaign_id = "test-ig-001"
    campaign_dir = temp_data_dir / "campaigns" / "generated" / campaign_id
    campaign_dir.mkdir(parents=True)

    # Copy image to campaign directory
    campaign_image = campaign_dir / "image.jpg"
    shutil.copy(sample_image, campaign_image)

    metadata = {
        "id": campaign_id,
        "company_name": "Test Company IG",
        "event_name": "Test Event",
        "status": "pending",
        "platforms": ["instagram"],
        "instagram_account_id": "987654321",
        "caption": "Test Instagram post from integration test #test",
        "image_path": str(campaign_image),
        "image_url": "https://example.com/test_image.jpg",  # Mock URL
        "generated_at": "2026-06-10T10:00:00Z",
        "scheduled_publish_date": "2026-06-10",
    }

    # Save metadata
    metadata_path = campaign_dir / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return metadata


@pytest.fixture
def sample_campaign_multi_platform(sample_image, temp_data_dir):
    """Sample multi-platform campaign with metadata."""
    campaign_id = "test-multi-001"
    campaign_dir = temp_data_dir / "campaigns" / "generated" / campaign_id
    campaign_dir.mkdir(parents=True)

    # Copy image to campaign directory
    campaign_image = campaign_dir / "image.jpg"
    shutil.copy(sample_image, campaign_image)

    metadata = {
        "id": campaign_id,
        "company_name": "Test Company Multi",
        "event_name": "Test Event",
        "status": "pending",
        "platforms": ["facebook", "instagram"],
        "facebook_page_id": "123456789",
        "instagram_account_id": "987654321",
        "caption": "Test multi-platform post",
        "image_path": str(campaign_image),
        "image_url": "https://example.com/test_image.jpg",
        "generated_at": "2026-06-10T10:00:00Z",
        "scheduled_publish_date": "2026-06-10",
    }

    # Save metadata
    metadata_path = campaign_dir / "metadata.json"
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    return metadata


# ==========================================
# Generator Flow Fixtures
# ==========================================


@pytest.fixture
def sample_company_dental():
    """Sample dental company profile."""
    return {
        "slug": "test_dental",
        "name": "Test Dental Practice",
        "industry": "dental",
        "tone": "professional",
        "brand_colors": ["#0066cc", "#ffffff"],
        "facebook_page_id": "dental_fb_123",
        "instagram_account_id": "dental_ig_456",
        "active": True,
    }


@pytest.fixture
def sample_company_restaurant():
    """Sample restaurant company profile."""
    return {
        "slug": "test_restaurant",
        "name": "Test Restaurant",
        "industry": "restaurant",
        "tone": "friendly",
        "brand_colors": ["#ff6600", "#ffffff"],
        "facebook_page_id": "restaurant_fb_789",
        "instagram_account_id": "restaurant_ig_012",
        "active": True,
    }


@pytest.fixture
def sample_event_valentines():
    """Sample universal holiday event (Valentine's Day)."""
    # 10 days from now to match generation_lead_days
    event_date = (datetime.now() + timedelta(days=10)).date()
    return {
        "name": "Valentine's Day",
        "date": event_date.isoformat(),
        "tags": ["holiday", "seasonal"],
        "description": "Day of love and romance",
    }


@pytest.fixture
def sample_event_oral_health():
    """Sample dental-specific event."""
    event_date = (datetime.now() + timedelta(days=10)).date()
    return {
        "name": "National Oral Health Month",
        "date": event_date.isoformat(),
        "tags": ["health", "awareness"],
        "description": "Promoting oral health awareness",
    }


@pytest.fixture
def sample_event_food_day():
    """Sample restaurant-specific event."""
    event_date = (datetime.now() + timedelta(days=10)).date()
    return {
        "name": "National Food Day",
        "date": event_date.isoformat(),
        "tags": ["culinary"],
        "description": "Celebrating food and cuisine",
    }


@pytest.fixture
def sample_event_irrelevant():
    """Sample irrelevant event (automotive) for testing filtering."""
    event_date = (datetime.now() + timedelta(days=10)).date()
    return {
        "name": "Auto Show Event",
        "date": event_date.isoformat(),
        "tags": ["automotive"],
        "description": "Annual automotive exhibition",
    }


@pytest.fixture
def sample_logo_dental(temp_data_dir):
    """Create a sample dental logo (100x100 blue square with white rectangle)."""
    img = Image.new("RGB", (100, 100), color="#0066cc")
    draw = ImageDraw.Draw(img)
    # Add white rectangle to make it recognizable
    draw.rectangle([20, 40, 80, 60], fill="white")

    logo_path = temp_data_dir / "test_dental_logo.png"
    img.save(logo_path, "PNG")

    yield logo_path

    # Clean up
    if logo_path.exists():
        logo_path.unlink()


@pytest.fixture
def sample_logo_restaurant(temp_data_dir):
    """Create a sample restaurant logo (100x100 red circle on white background)."""
    img = Image.new("RGB", (100, 100), color="white")
    draw = ImageDraw.Draw(img)
    # Add red circle
    draw.ellipse([10, 10, 90, 90], fill="#ff6600")

    logo_path = temp_data_dir / "test_restaurant_logo.png"
    img.save(logo_path, "PNG")

    yield logo_path

    # Clean up
    if logo_path.exists():
        logo_path.unlink()


@pytest.fixture
def mock_generated_image():
    """Create a mock DALL-E generated image (1024x1024 gradient)."""
    # Create a simple gradient image using PIL only
    img = Image.new("RGB", (1024, 1024))
    pixels = img.load()

    # Create a diagonal gradient
    for x in range(1024):
        for y in range(1024):
            # Gradient from top-left (dark) to bottom-right (bright)
            red = int((x / 1024) * 255)
            green = int((y / 1024) * 255)
            blue = 128
            pixels[x, y] = (red, green, blue)

    return img


@pytest.fixture
def temp_data_dir_with_structure(
    temp_data_dir,
    sample_company_dental,
    sample_company_restaurant,
    sample_logo_dental,
    sample_logo_restaurant,
    sample_event_valentines,
    sample_event_oral_health,
    sample_event_food_day,
    sample_event_irrelevant,
    monkeypatch,
):
    """
    Create full test data structure with companies, logos, events, and registry.
    Patches all relevant settings paths.
    """
    # Create directory structure
    companies_dir = temp_data_dir / "companies"
    companies_dir.mkdir(parents=True, exist_ok=True)

    events_dir = temp_data_dir / "events"
    events_dir.mkdir(parents=True, exist_ok=True)

    registry_dir = temp_data_dir / "registry"
    registry_dir.mkdir(parents=True, exist_ok=True)

    # Create dental company directory
    dental_dir = companies_dir / "test_dental"
    dental_dir.mkdir(parents=True, exist_ok=True)

    # Save dental company profile
    with open(dental_dir / "profile.json", "w") as f:
        json.dump(sample_company_dental, f, indent=2)

    # Copy dental logo
    shutil.copy(sample_logo_dental, dental_dir / "logo.png")

    # Create restaurant company directory
    restaurant_dir = companies_dir / "test_restaurant"
    restaurant_dir.mkdir(parents=True, exist_ok=True)

    # Save restaurant company profile
    with open(restaurant_dir / "profile.json", "w") as f:
        json.dump(sample_company_restaurant, f, indent=2)

    # Copy restaurant logo
    shutil.copy(sample_logo_restaurant, restaurant_dir / "logo.png")

    # Create company registry
    registry = {
        "companies": [
            {"slug": "test_dental", "active": True},
            {"slug": "test_restaurant", "active": True},
        ]
    }
    registry_path = registry_dir / "company_registry.json"
    with open(registry_path, "w") as f:
        json.dump(registry, f, indent=2)

    # Create events for 2026, preserving any pre-existing file so git stays clean
    current_year = datetime.now().year
    events_2026 = [
        sample_event_valentines,
        sample_event_oral_health,
        sample_event_food_day,
        sample_event_irrelevant,
    ]
    events_file = events_dir / f"{current_year}.json"
    original_events_content = events_file.read_text() if events_file.exists() else None
    with open(events_file, "w") as f:
        json.dump(events_2026, f, indent=2)

    # Patch all settings paths
    monkeypatch.setattr("app.core.config.settings.data_dir", str(temp_data_dir))
    monkeypatch.setattr("app.core.config.settings.companies_dir", str(companies_dir))
    monkeypatch.setattr("app.core.config.settings.registry_path", str(registry_path))
    monkeypatch.setattr("app.core.config.settings.events_dir", str(events_dir))

    yield temp_data_dir

    # Restore the original events file so the working tree stays clean
    if original_events_content is not None:
        events_file.write_text(original_events_content)
    elif events_file.exists():
        events_file.unlink()
