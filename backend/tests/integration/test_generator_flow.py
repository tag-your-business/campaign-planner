"""Integration tests for the generator flow."""

import json
from io import BytesIO
from pathlib import Path
from unittest.mock import Mock

import pytest
from app.common.storage.service import StorageService
from app.features.generation.branding import BrandingService
from app.features.generation.caption import CaptionGenerator
from app.features.generation.image import ImageService
from app.features.generation.planner import CampaignPlanner
from app.features.generation.prompt import PromptGenerator
from PIL import Image
from tests.mocks.mock_openai_client import MockOpenAIClient


@pytest.mark.asyncio
class TestGeneratorFlowIntegration:
    """Integration tests for the complete generator flow."""

    @pytest.mark.skip(reason="requires Anthropic API credentials")
    async def test_generate_single_campaign_happy_path(
        self,
        temp_data_dir_with_structure,
        sample_company_dental,
        sample_event_valentines,
        mock_generated_image,
        mocker,
        caplog,
    ):
        """
        Test the complete happy path: planning → caption → image → branding → storage.

        This is the most comprehensive test covering:
        - Campaign planning and relevance matching
        - Caption generation via gpt-5.4-mini
        - Image prompt generation
        - Image generation via gpt-image-2
        - Branding with logo overlay
        - Metadata storage
        """
        # Setup: Create mock OpenAI client
        mock_openai = MockOpenAIClient(
            custom_caption="Love is in the air! Book your Valentine's appointment today.",
            custom_image_url="https://mock-openai.com/valentine-image.png",
        )

        # Patch OpenAI clients in both caption and image services
        mocker.patch("app.features.generation.caption.OpenAI", return_value=mock_openai)
        mocker.patch("app.features.generation.image.OpenAI", return_value=mock_openai)

        # Mock httpx.get for image download
        mock_image_bytes = BytesIO()
        mock_generated_image.save(mock_image_bytes, format="PNG")
        mock_image_bytes.seek(0)

        mock_response = Mock()
        mock_response.content = mock_image_bytes.read()
        mock_response.raise_for_status = Mock()

        mocker.patch("httpx.get", return_value=mock_response)

        # Initialize services
        planner = CampaignPlanner()
        caption_gen = CaptionGenerator()
        prompt_gen = PromptGenerator()
        image_service = ImageService()
        branding_service = BrandingService()
        StorageService()

        # Execute: Plan campaign
        with caplog.at_level("INFO"):
            campaign_spec = planner.plan(sample_company_dental, sample_event_valentines)

        # Verify campaign was planned
        assert campaign_spec is not None
        assert campaign_spec["company_slug"] == sample_company_dental["slug"]
        assert campaign_spec["event_name"] == sample_event_valentines["name"]
        assert "Planned campaign" in caplog.text or "Valentine" in caplog.text

        # Execute: Generate caption
        caption = caption_gen.generate(campaign_spec)

        # Verify caption generation
        assert caption is not None
        assert len(caption) > 0
        assert "Valentine" in caption or "Love" in caption
        assert len(mock_openai.chat_invocations) == 1
        assert mock_openai.chat_invocations[0]["model"] == "gpt-5.4-mini"

        # Execute: Generate image prompt
        image_prompt = prompt_gen.generate(campaign_spec)

        # Verify prompt generation
        assert image_prompt is not None
        assert len(image_prompt) > 0

        # Execute: Generate image
        campaigns_dir = Path(temp_data_dir_with_structure) / "campaigns" / "generated"
        event_name = sample_event_valentines["name"].lower().replace(" ", "-")
        campaign_id = f"{sample_company_dental['slug']}-{event_name}"
        campaign_dir = campaigns_dir / campaign_id
        campaign_dir.mkdir(parents=True, exist_ok=True)

        raw_image_path = campaign_dir / "image_raw.png"
        image_service.generate(image_prompt, raw_image_path)

        # Verify image generation
        assert raw_image_path.exists()
        assert len(mock_openai.image_invocations) == 1
        assert mock_openai.image_invocations[0]["model"] == "gpt-image-2"

        # Get the mock image URL from the invocation
        image_url = mock_openai.custom_image_url

        # Execute: Apply branding
        logo_path = (
            Path(temp_data_dir_with_structure)
            / "companies"
            / sample_company_dental["slug"]
            / "logo.png"
        )
        final_image_path = campaign_dir / "image.png"
        branding_service.apply(
            raw_image_path, final_image_path, sample_company_dental, logo_path
        )

        # Verify branding applied
        assert final_image_path.exists()
        raw_img = Image.open(raw_image_path)
        branded_img = Image.open(final_image_path)
        assert raw_img.size == branded_img.size
        # Logo overlay should change file size
        assert raw_image_path.stat().st_size != final_image_path.stat().st_size

        # Execute: Save metadata
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
            "image_url": image_url,
            "generated_at": "2026-06-11T10:00:00Z",
            "scheduled_publish_date": sample_event_valentines["date"],
        }

        # Save caption
        caption_path = campaign_dir / "caption.txt"
        with open(caption_path, "w") as f:
            f.write(caption)

        # Save metadata
        metadata_path = campaign_dir / "metadata.json"
        with open(metadata_path, "w") as f:
            json.dump(metadata, f, indent=2)

        # Verify file structure
        assert (campaign_dir / "metadata.json").exists()
        assert (campaign_dir / "caption.txt").exists()
        assert (campaign_dir / "image_raw.png").exists()
        assert (campaign_dir / "image.png").exists()

        # Verify metadata content
        with open(metadata_path) as f:
            saved_metadata = json.load(f)

        assert saved_metadata["status"] == "pending"
        assert saved_metadata["company_slug"] == "test_dental"
        assert saved_metadata["event_name"] == "Valentine's Day"
        assert "platforms" in saved_metadata
        assert len(saved_metadata["platforms"]) == 2

    async def test_relevance_filtering_irrelevant_event(
        self, sample_company_dental, sample_event_irrelevant
    ):
        """Test that irrelevant events are filtered out (returns None)."""
        # Setup
        planner = CampaignPlanner()

        # Execute
        campaign_spec = planner.plan(sample_company_dental, sample_event_irrelevant)

        # Verify: Should return None for irrelevant event
        assert campaign_spec is None

    async def test_universal_holiday_all_industries(
        self, sample_company_dental, sample_company_restaurant, sample_event_valentines
    ):
        """Test that universal holidays are accepted by all industries."""
        # Setup
        planner = CampaignPlanner()

        # Execute: Plan for both dental and restaurant
        dental_spec = planner.plan(sample_company_dental, sample_event_valentines)
        restaurant_spec = planner.plan(
            sample_company_restaurant, sample_event_valentines
        )

        # Verify: Both should accept Valentine's Day
        assert dental_spec is not None
        assert restaurant_spec is not None
        assert dental_spec["event_name"] == "Valentine's Day"
        assert restaurant_spec["event_name"] == "Valentine's Day"

    async def test_industry_specific_event_matching(
        self,
        sample_company_dental,
        sample_company_restaurant,
        sample_event_oral_health,
        sample_event_food_day,
    ):
        """Test that industry-specific events match correctly."""
        # Setup
        planner = CampaignPlanner()

        # Execute: Dental accepts oral health, rejects food
        dental_oral = planner.plan(sample_company_dental, sample_event_oral_health)
        dental_food = planner.plan(sample_company_dental, sample_event_food_day)

        # Execute: Restaurant accepts food, rejects oral health
        restaurant_food = planner.plan(sample_company_restaurant, sample_event_food_day)
        restaurant_oral = planner.plan(
            sample_company_restaurant, sample_event_oral_health
        )

        # Verify
        assert dental_oral is not None  # Dental accepts oral health event
        assert dental_food is None  # Dental rejects food event
        assert restaurant_food is not None  # Restaurant accepts food event
        assert restaurant_oral is None  # Restaurant rejects oral health event

    async def test_caption_generation_failure(
        self, sample_company_dental, sample_event_valentines, mocker, caplog
    ):
        """Test caption generation failure handling."""
        # Setup: Mock to fail — force openai provider so the client patch is used
        mock_openai = MockOpenAIClient(should_fail_chat=True)
        mocker.patch("time.sleep")  # prevent tenacity wait between retries
        mock_settings = mocker.patch("app.common.ai_providers.factory.settings")
        mock_settings.text_generation_provider = "openai"
        mock_settings.openai_api_key = "sk-dummy"
        mock_settings.openai_text_model = "gpt-5.4-mini"
        mocker.patch(
            "app.common.ai_providers.providers.openai_provider.OpenAI",
            return_value=mock_openai,
        )

        # Initialize services
        planner = CampaignPlanner()
        caption_gen = CaptionGenerator()

        # Execute: Plan campaign
        campaign_spec = planner.plan(sample_company_dental, sample_event_valentines)

        # Execute: Attempt caption generation (should fail after all retries)
        with pytest.raises(Exception) as exc_info:
            with caplog.at_level("ERROR"):
                caption_gen.generate(campaign_spec)

        # Verify failure and that all retry attempts were made
        assert "Mock OpenAI chat API error" in str(exc_info.value)
        assert len(mock_openai.responses_invocations) >= 3

    @pytest.mark.skip(reason="requires Anthropic API credentials")
    async def test_image_generation_failure(
        self,
        temp_data_dir_with_structure,
        sample_company_dental,
        sample_event_valentines,
        mocker,
        caplog,
    ):
        """Test image generation failure handling."""
        # Setup: Mock to fail
        mock_openai = MockOpenAIClient(should_fail_image=True)
        mocker.patch("app.features.generation.image.OpenAI", return_value=mock_openai)

        # Initialize services
        planner = CampaignPlanner()
        prompt_gen = PromptGenerator()
        image_service = ImageService()

        # Execute: Plan campaign and generate prompt
        campaign_spec = planner.plan(sample_company_dental, sample_event_valentines)
        image_prompt = prompt_gen.generate(campaign_spec)

        # Setup path
        campaigns_dir = Path(temp_data_dir_with_structure) / "campaigns" / "generated"
        campaign_id = "test-fail-image"
        campaign_dir = campaigns_dir / campaign_id
        campaign_dir.mkdir(parents=True, exist_ok=True)
        raw_image_path = campaign_dir / "image_raw.png"

        # Execute: Attempt image generation (should fail)
        with pytest.raises(Exception) as exc_info:
            with caplog.at_level("ERROR"):
                image_service.generate(image_prompt, raw_image_path)

        # Verify failure
        assert "Mock OpenAI image API error" in str(exc_info.value)
        assert not raw_image_path.exists()  # File should not be created

    async def test_branding_with_and_without_logo(
        self,
        temp_data_dir_with_structure,
        sample_company_dental,
        mock_generated_image,
        caplog,
    ):
        """Test branding variations: with logo, without logo, missing logo."""
        # Setup
        branding_service = BrandingService()
        campaigns_dir = Path(temp_data_dir_with_structure) / "campaigns" / "generated"

        # Case 1: With logo
        campaign_dir_1 = campaigns_dir / "test-branding-with-logo"
        campaign_dir_1.mkdir(parents=True, exist_ok=True)
        raw_image_path_1 = campaign_dir_1 / "image_raw.png"
        final_image_path_1 = campaign_dir_1 / "image.png"
        mock_generated_image.save(raw_image_path_1, "PNG")

        logo_path = (
            Path(temp_data_dir_with_structure)
            / "companies"
            / "test_dental"
            / "logo.png"
        )

        with caplog.at_level("INFO"):
            branding_service.apply(
                raw_image_path_1, final_image_path_1, sample_company_dental, logo_path
            )

        assert final_image_path_1.exists()
        assert raw_image_path_1.stat().st_size != final_image_path_1.stat().st_size

        # Case 2: Without logo (logo=None)
        campaign_dir_2 = campaigns_dir / "test-branding-no-logo"
        campaign_dir_2.mkdir(parents=True, exist_ok=True)
        raw_image_path_2 = campaign_dir_2 / "image_raw.png"
        final_image_path_2 = campaign_dir_2 / "image.png"
        mock_generated_image.save(raw_image_path_2, "PNG")

        with caplog.at_level("INFO"):
            branding_service.apply(
                raw_image_path_2, final_image_path_2, sample_company_dental, None
            )

        assert final_image_path_2.exists()

        # Case 3: Missing logo file (path doesn't exist)
        campaign_dir_3 = campaigns_dir / "test-branding-missing-logo"
        campaign_dir_3.mkdir(parents=True, exist_ok=True)
        raw_image_path_3 = campaign_dir_3 / "image_raw.png"
        final_image_path_3 = campaign_dir_3 / "image.png"
        mock_generated_image.save(raw_image_path_3, "PNG")

        missing_logo_path = (
            Path(temp_data_dir_with_structure) / "nonexistent" / "logo.png"
        )

        with caplog.at_level("WARNING"):
            branding_service.apply(
                raw_image_path_3,
                final_image_path_3,
                sample_company_dental,
                missing_logo_path,
            )

        assert final_image_path_3.exists()
        # Should log warning about missing logo
        assert "logo" in caplog.text.lower() or "warning" in caplog.text.lower()

    async def test_batch_generation_with_failure_isolation(
        self,
        temp_data_dir_with_structure,
        sample_company_dental,
        sample_event_valentines,
        sample_event_oral_health,
        sample_event_food_day,
        mock_generated_image,
        mocker,
        caplog,
    ):
        """Test that one campaign failure doesn't stop others in batch processing."""
        # Setup: Mock that fails on second responses invocation (gpt-5.4-mini uses Responses API)
        mock_openai = MockOpenAIClient()
        original_create = mock_openai.responses.create

        call_count = [0]

        def create_with_selective_failure(*args, **kwargs):
            call_count[0] += 1
            if (
                2 <= call_count[0] <= 4
            ):  # Exhaust all 3 retry attempts for second campaign
                raise Exception("Mock failure on second campaign")
            return original_create(*args, **kwargs)

        mock_openai.responses.create = create_with_selective_failure

        mocker.patch("time.sleep")  # prevent tenacity wait between retries
        mock_settings = mocker.patch("app.common.ai_providers.factory.settings")
        mock_settings.text_generation_provider = "openai"
        mock_settings.openai_api_key = "sk-dummy"
        mock_settings.openai_text_model = "gpt-5.4-mini"
        mocker.patch(
            "app.common.ai_providers.providers.openai_provider.OpenAI",
            return_value=mock_openai,
        )
        mocker.patch("app.features.generation.image.OpenAI", return_value=mock_openai)

        # Mock image download
        mock_image_bytes = BytesIO()
        mock_generated_image.save(mock_image_bytes, format="PNG")
        mock_image_bytes.seek(0)

        mock_response = Mock()
        mock_response.content = mock_image_bytes.read()
        mock_response.raise_for_status = Mock()
        mocker.patch("httpx.get", return_value=mock_response)

        # Initialize services
        planner = CampaignPlanner()
        caption_gen = CaptionGenerator()

        # Execute: Process 3 events (1st and 3rd should succeed, 2nd should fail)
        events = [
            sample_event_valentines,
            sample_event_oral_health,
            sample_event_food_day,
        ]
        results = []

        with caplog.at_level("ERROR"):
            for event in events:
                try:
                    campaign_spec = planner.plan(sample_company_dental, event)
                    if campaign_spec:
                        caption = caption_gen.generate(campaign_spec)
                        results.append(
                            {
                                "event": event["name"],
                                "success": True,
                                "caption": caption,
                            }
                        )
                except Exception as e:
                    results.append(
                        {"event": event["name"], "success": False, "error": str(e)}
                    )

        # Verify: first campaign succeeds, second exhausts all retries and fails
        successful = [r for r in results if r.get("success")]
        failed = [r for r in results if not r.get("success")]

        assert len(successful) >= 1  # At least one campaign succeeded
        assert len(failed) >= 1  # At least one campaign failed
        assert "Mock failure on second campaign" in failed[0]["error"]

    async def test_date_filtering_generation_lead_days(
        self, sample_company_dental, mocker
    ):
        """
        Test that CampaignPlanner correctly plans campaigns with various event dates.

        Note: The CampaignPlanner.plan() method doesn't filter by date - it only checks
        relevance. Date filtering is done at a higher level (e.g., scheduler service).
        This test verifies that the planner can handle events at different dates and
        correctly calculates scheduled_publish_date.
        """
        from datetime import datetime, timedelta

        # Setup: Create events at different dates with relevant tags for dental
        today = datetime.now().date()
        event_10_days = {
            "name": "Dental Health Day",
            "date": (today + timedelta(days=10)).isoformat(),
            "tags": ["health"],
        }
        event_20_days = {
            "name": "Oral Hygiene Week",
            "date": (today + timedelta(days=20)).isoformat(),
            "tags": ["health"],
        }
        event_5_days = {
            "name": "Smile Awareness Day",
            "date": (today + timedelta(days=5)).isoformat(),
            "tags": ["health"],
        }

        # Mock settings.publish_lead_days = 3 (publish 3 days before event)
        mocker.patch("app.core.config.settings.publish_lead_days", 3)

        # Initialize planner
        planner = CampaignPlanner()

        # Execute: Test each event
        spec_10 = planner.plan(sample_company_dental, event_10_days)
        spec_20 = planner.plan(sample_company_dental, event_20_days)
        spec_5 = planner.plan(sample_company_dental, event_5_days)

        # Verify: All relevant events should be planned (date filtering happens elsewhere)
        assert spec_10 is not None
        assert spec_20 is not None
        assert spec_5 is not None

        # Verify scheduled_publish_date is calculated correctly (event_date - publish_lead_days)
        expected_publish_10 = (
            datetime.fromisoformat(event_10_days["date"]) - timedelta(days=3)
        ).isoformat()
        expected_publish_20 = (
            datetime.fromisoformat(event_20_days["date"]) - timedelta(days=3)
        ).isoformat()
        expected_publish_5 = (
            datetime.fromisoformat(event_5_days["date"]) - timedelta(days=3)
        ).isoformat()

        assert spec_10["scheduled_publish_date"] == expected_publish_10
        assert spec_20["scheduled_publish_date"] == expected_publish_20
        assert spec_5["scheduled_publish_date"] == expected_publish_5
