"""Unit tests for generate_scheduler — all I/O and generators are mocked."""

import json
from unittest.mock import MagicMock, patch

import pytest
from app.schedulers.generate_scheduler import (
    _load_existing_metadata,
    _process_campaign,
    _run_caption_step,
    _run_image_step,
    _run_prompt_step,
)

# ---------------------------------------------------------------------------
# Shared test data
# ---------------------------------------------------------------------------

CAMPAIGN_SPEC = {
    "company_slug": "acme",
    "event_id": "new-years",
    "event_name": "New Year",
    "company_name": "Acme Corp",
    "industry": "retail",
    "tone": "friendly",
    "brand_colors": ["#FF0000"],
    "platforms": ["facebook", "instagram"],
    "scheduled_publish_date": "2026-12-31",
    "facebook_page_id": "123",
    "instagram_account_id": "456",
}

COMPANY = {
    "slug": "acme",
    "name": "Acme Corp",
    "industry": "retail",
    "tone": "friendly",
}

EVENT = {
    "id": "new-years",
    "name": "New Year",
    "date": "2026-01-01",
}

FULL_METADATA = {
    "id": "acme_new-years_20260101_080000",
    "company_slug": "acme",
    "company_name": "Acme Corp",
    "event_id": "new-years",
    "event_name": "New Year",
    "event_date": "2026-01-01",
    "generated_at": "2026-01-01T08:00:00",
    "last_attempted_at": "2026-01-01T08:00:00",
    "scheduled_publish_date": "2026-12-31",
    "status": "pending",
    "caption": "Happy New Year! #NewYear",
    "image_prompt": "Fireworks over a city skyline",
    "image_path": "/data/campaigns/generated/acme_new-years_20260101_080000/image.png",
    "platforms": ["facebook", "instagram"],
    "facebook_page_id": "123",
    "instagram_account_id": "456",
}


# ---------------------------------------------------------------------------
# _load_existing_metadata
# ---------------------------------------------------------------------------


class TestLoadExistingMetadata:
    def test_returns_none_when_base_dir_missing(self, tmp_path):
        result = _load_existing_metadata(
            str(tmp_path / "campaigns"), "acme", "new-years"
        )
        assert result is None

    def test_returns_none_when_no_matching_folder(self, tmp_path):
        generated = tmp_path / "generated"
        generated.mkdir(parents=True)
        (generated / "other_slug_event_20260101").mkdir()
        result = _load_existing_metadata(str(tmp_path), "acme", "new-years")
        assert result is None

    def test_returns_none_when_folder_has_no_metadata(self, tmp_path):
        generated = tmp_path / "generated"
        (generated / "acme_new-years_20260101").mkdir(parents=True)
        result = _load_existing_metadata(str(tmp_path), "acme", "new-years")
        assert result is None

    def test_returns_metadata_when_found(self, tmp_path):
        folder = tmp_path / "generated" / "acme_new-years_20260101"
        folder.mkdir(parents=True)
        (folder / "metadata.json").write_text(json.dumps(FULL_METADATA))
        result = _load_existing_metadata(str(tmp_path), "acme", "new-years")
        assert result == FULL_METADATA

    def test_matches_by_prefix(self, tmp_path):
        folder = tmp_path / "generated" / "acme_new-years_20260101_080000"
        folder.mkdir(parents=True)
        (folder / "metadata.json").write_text(json.dumps(FULL_METADATA))
        result = _load_existing_metadata(str(tmp_path), "acme", "new-years")
        assert result["id"] == FULL_METADATA["id"]

    def test_does_not_match_partial_slug(self, tmp_path):
        folder = tmp_path / "generated" / "acme-extra_new-years_20260101"
        folder.mkdir(parents=True)
        (folder / "metadata.json").write_text(json.dumps(FULL_METADATA))
        result = _load_existing_metadata(str(tmp_path), "acme", "new-years")
        assert result is None


# ---------------------------------------------------------------------------
# _run_caption_step
# ---------------------------------------------------------------------------


class TestRunCaptionStep:
    def test_skips_when_existing_caption_present(self, tmp_path):
        caption_gen = MagicMock()
        result = _run_caption_step(caption_gen, CAMPAIGN_SPEC, tmp_path, FULL_METADATA)
        assert result == {"success": True, "data": "Happy New Year! #NewYear"}
        caption_gen.generate.assert_not_called()

    def test_generates_when_caption_missing(self, tmp_path):
        caption_gen = MagicMock()
        caption_gen.generate.return_value = "Fresh caption #NewYear"
        metadata = {**FULL_METADATA, "caption": ""}
        result = _run_caption_step(caption_gen, CAMPAIGN_SPEC, tmp_path, metadata)
        assert result == {"success": True, "data": "Fresh caption #NewYear"}

    def test_generates_when_no_existing_metadata(self, tmp_path):
        caption_gen = MagicMock()
        caption_gen.generate.return_value = "First caption"
        result = _run_caption_step(caption_gen, CAMPAIGN_SPEC, tmp_path, None)
        assert result["success"] is True
        assert result["data"] == "First caption"

    def test_writes_caption_txt_on_success(self, tmp_path):
        caption_gen = MagicMock()
        caption_gen.generate.return_value = "Saved caption 🌞"
        _run_caption_step(caption_gen, CAMPAIGN_SPEC, tmp_path, None)
        assert (tmp_path / "caption.txt").read_text(
            encoding="utf-8"
        ) == "Saved caption 🌞"

    def test_returns_failure_dict_on_exception(self, tmp_path):
        caption_gen = MagicMock()
        caption_gen.generate.side_effect = Exception("API error")
        result = _run_caption_step(caption_gen, CAMPAIGN_SPEC, tmp_path, None)
        assert result == {"success": False, "data": ""}

    def test_does_not_write_file_on_failure(self, tmp_path):
        caption_gen = MagicMock()
        caption_gen.generate.side_effect = Exception("API error")
        _run_caption_step(caption_gen, CAMPAIGN_SPEC, tmp_path, None)
        assert not (tmp_path / "caption.txt").exists()


# ---------------------------------------------------------------------------
# _run_prompt_step
# ---------------------------------------------------------------------------


class TestRunPromptStep:
    def test_skips_when_existing_prompt_present(self):
        prompt_gen = MagicMock()
        result = _run_prompt_step(prompt_gen, CAMPAIGN_SPEC, FULL_METADATA)
        assert result == {"success": True, "data": "Fireworks over a city skyline"}
        prompt_gen.generate.assert_not_called()

    def test_generates_when_prompt_missing(self):
        prompt_gen = MagicMock()
        prompt_gen.generate.return_value = "New prompt"
        metadata = {**FULL_METADATA, "image_prompt": ""}
        result = _run_prompt_step(prompt_gen, CAMPAIGN_SPEC, metadata)
        assert result == {"success": True, "data": "New prompt"}

    def test_generates_when_no_existing_metadata(self):
        prompt_gen = MagicMock()
        prompt_gen.generate.return_value = "First prompt"
        result = _run_prompt_step(prompt_gen, CAMPAIGN_SPEC, None)
        assert result == {"success": True, "data": "First prompt"}

    def test_returns_failure_dict_on_exception(self):
        prompt_gen = MagicMock()
        prompt_gen.generate.side_effect = Exception("LLM error")
        result = _run_prompt_step(prompt_gen, CAMPAIGN_SPEC, None)
        assert result == {"success": False, "data": ""}


# ---------------------------------------------------------------------------
# _run_image_step
# ---------------------------------------------------------------------------


class TestRunImageStep:
    def test_skips_when_image_exists_on_disk(self, tmp_path):
        image_file = tmp_path / "image.png"
        image_file.write_bytes(b"PNG")
        metadata = {**FULL_METADATA, "image_path": str(image_file)}
        image_service = MagicMock()
        branding_service = MagicMock()
        result = _run_image_step(
            image_service, branding_service, "a prompt", tmp_path, None, metadata
        )
        assert result == {"success": True, "data": str(image_file)}
        image_service.generate.assert_not_called()

    def test_regenerates_when_image_path_missing(self, tmp_path):
        metadata = {**FULL_METADATA, "image_path": ""}
        image_service = MagicMock()
        branding_service = MagicMock()
        branding_service.apply.return_value = tmp_path / "image.png"
        result = _run_image_step(
            image_service, branding_service, "a prompt", tmp_path, None, metadata
        )
        assert result["success"] is True
        image_service.generate.assert_called_once()

    def test_regenerates_when_image_file_deleted(self, tmp_path):
        metadata = {**FULL_METADATA, "image_path": str(tmp_path / "image.png")}
        image_service = MagicMock()
        branding_service = MagicMock()
        result = _run_image_step(
            image_service, branding_service, "a prompt", tmp_path, None, metadata
        )
        assert result["success"] is True
        image_service.generate.assert_called_once()

    def test_skips_when_no_prompt(self, tmp_path):
        image_service = MagicMock()
        branding_service = MagicMock()
        result = _run_image_step(
            image_service, branding_service, "", tmp_path, None, None
        )
        assert result == {"success": False, "data": ""}
        image_service.generate.assert_not_called()

    def test_returns_branded_image_path_on_success(self, tmp_path):
        image_service = MagicMock()
        branding_service = MagicMock()
        result = _run_image_step(
            image_service, branding_service, "a prompt", tmp_path, None, None
        )
        assert result["success"] is True
        assert result["data"] == str(tmp_path / "image.png")

    def test_returns_failure_dict_on_image_service_error(self, tmp_path):
        image_service = MagicMock()
        image_service.generate.side_effect = Exception("DALL-E error")
        branding_service = MagicMock()
        result = _run_image_step(
            image_service, branding_service, "a prompt", tmp_path, None, None
        )
        assert result == {"success": False, "data": ""}

    def test_returns_failure_dict_on_branding_error(self, tmp_path):
        image_service = MagicMock()
        branding_service = MagicMock()
        branding_service.apply.side_effect = Exception("Pillow error")
        result = _run_image_step(
            image_service, branding_service, "a prompt", tmp_path, None, None
        )
        assert result == {"success": False, "data": ""}

    def test_passes_logo_path_to_branding(self, tmp_path):
        logo = tmp_path / "logo.png"
        logo.write_bytes(b"PNG")
        image_service = MagicMock()
        branding_service = MagicMock()
        _run_image_step(
            image_service, branding_service, "a prompt", tmp_path, logo, None
        )
        branding_service.apply.assert_called_once()
        _, call_logo, _ = branding_service.apply.call_args[0]
        assert call_logo == logo


# ---------------------------------------------------------------------------
# _process_campaign
# ---------------------------------------------------------------------------


def _make_services(caption="Generated caption", image_prompt="Generated prompt"):
    storage = MagicMock()
    planner = MagicMock()
    planner.plan.return_value = CAMPAIGN_SPEC
    caption_gen = MagicMock()
    caption_gen.generate.return_value = caption
    prompt_gen = MagicMock()
    prompt_gen.generate.return_value = image_prompt
    image_service = MagicMock()
    branding_service = MagicMock()
    return storage, planner, caption_gen, prompt_gen, image_service, branding_service


@pytest.fixture
def services():
    return _make_services()


class TestProcessCampaignFullSuccess:
    def test_returns_true_when_all_steps_succeed(self, tmp_path, services):
        storage, planner, caption_gen, prompt_gen, image_service, branding_service = (
            services
        )
        with patch(
            "app.schedulers.generate_scheduler._load_existing_metadata",
            return_value=None,
        ), patch("app.schedulers.generate_scheduler.settings") as mock_settings:
            mock_settings.campaigns_dir = str(tmp_path)
            mock_settings.companies_dir = str(tmp_path / "companies")
            result = _process_campaign(
                storage,
                planner,
                caption_gen,
                prompt_gen,
                image_service,
                branding_service,
                COMPANY,
                EVENT,
            )
        assert result is True

    def test_saves_metadata_with_status_pending(self, tmp_path, services):
        storage, planner, caption_gen, prompt_gen, image_service, branding_service = (
            services
        )
        with patch(
            "app.schedulers.generate_scheduler._load_existing_metadata",
            return_value=None,
        ), patch("app.schedulers.generate_scheduler.settings") as mock_settings:
            mock_settings.campaigns_dir = str(tmp_path)
            mock_settings.companies_dir = str(tmp_path / "companies")
            _process_campaign(
                storage,
                planner,
                caption_gen,
                prompt_gen,
                image_service,
                branding_service,
                COMPANY,
                EVENT,
            )
        saved = storage.save_metadata.call_args[0][1]
        assert saved["status"] == "pending"

    def test_metadata_contains_generated_values(self, tmp_path, services):
        storage, planner, caption_gen, prompt_gen, image_service, branding_service = (
            services
        )
        caption_gen.generate.return_value = "Happy New Year!"
        prompt_gen.generate.return_value = "Fireworks image"
        with patch(
            "app.schedulers.generate_scheduler._load_existing_metadata",
            return_value=None,
        ), patch("app.schedulers.generate_scheduler.settings") as mock_settings:
            mock_settings.campaigns_dir = str(tmp_path)
            mock_settings.companies_dir = str(tmp_path / "companies")
            _process_campaign(
                storage,
                planner,
                caption_gen,
                prompt_gen,
                image_service,
                branding_service,
                COMPANY,
                EVENT,
            )
        saved = storage.save_metadata.call_args[0][1]
        assert saved["caption"] == "Happy New Year!"
        assert saved["image_prompt"] == "Fireworks image"


class TestProcessCampaignPartialFailure:
    def test_returns_false_when_caption_fails(self, tmp_path, services):
        storage, planner, caption_gen, prompt_gen, image_service, branding_service = (
            services
        )
        caption_gen.generate.side_effect = Exception("caption API down")
        with patch(
            "app.schedulers.generate_scheduler._load_existing_metadata",
            return_value=None,
        ), patch("app.schedulers.generate_scheduler.settings") as mock_settings:
            mock_settings.campaigns_dir = str(tmp_path)
            mock_settings.companies_dir = str(tmp_path / "companies")
            result = _process_campaign(
                storage,
                planner,
                caption_gen,
                prompt_gen,
                image_service,
                branding_service,
                COMPANY,
                EVENT,
            )
        assert result is False

    def test_saves_metadata_with_status_partial_on_failure(self, tmp_path, services):
        storage, planner, caption_gen, prompt_gen, image_service, branding_service = (
            services
        )
        caption_gen.generate.side_effect = Exception("caption API down")
        with patch(
            "app.schedulers.generate_scheduler._load_existing_metadata",
            return_value=None,
        ), patch("app.schedulers.generate_scheduler.settings") as mock_settings:
            mock_settings.campaigns_dir = str(tmp_path)
            mock_settings.companies_dir = str(tmp_path / "companies")
            _process_campaign(
                storage,
                planner,
                caption_gen,
                prompt_gen,
                image_service,
                branding_service,
                COMPANY,
                EVENT,
            )
        saved = storage.save_metadata.call_args[0][1]
        assert saved["status"] == "partial"
        assert saved["caption"] == ""

    def test_metadata_always_saved_even_on_failure(self, tmp_path, services):
        storage, planner, caption_gen, prompt_gen, image_service, branding_service = (
            services
        )
        caption_gen.generate.side_effect = Exception("all broken")
        prompt_gen.generate.side_effect = Exception("all broken")
        image_service.generate.side_effect = Exception("all broken")
        with patch(
            "app.schedulers.generate_scheduler._load_existing_metadata",
            return_value=None,
        ), patch("app.schedulers.generate_scheduler.settings") as mock_settings:
            mock_settings.campaigns_dir = str(tmp_path)
            mock_settings.companies_dir = str(tmp_path / "companies")
            _process_campaign(
                storage,
                planner,
                caption_gen,
                prompt_gen,
                image_service,
                branding_service,
                COMPANY,
                EVENT,
            )
        storage.save_metadata.assert_called_once()
        saved = storage.save_metadata.call_args[0][1]
        assert saved["caption"] == ""
        assert saved["image_prompt"] == ""
        assert saved["image_path"] == ""

    def test_image_step_skipped_when_prompt_fails(self, tmp_path, services):
        storage, planner, caption_gen, prompt_gen, image_service, branding_service = (
            services
        )
        prompt_gen.generate.side_effect = Exception("LLM down")
        with patch(
            "app.schedulers.generate_scheduler._load_existing_metadata",
            return_value=None,
        ), patch("app.schedulers.generate_scheduler.settings") as mock_settings:
            mock_settings.campaigns_dir = str(tmp_path)
            mock_settings.companies_dir = str(tmp_path / "companies")
            _process_campaign(
                storage,
                planner,
                caption_gen,
                prompt_gen,
                image_service,
                branding_service,
                COMPANY,
                EVENT,
            )
        image_service.generate.assert_not_called()


class TestProcessCampaignResume:
    def test_skips_fully_generated_campaign(self, tmp_path, services):
        storage, planner, caption_gen, prompt_gen, image_service, branding_service = (
            services
        )
        with patch(
            "app.schedulers.generate_scheduler._load_existing_metadata",
            return_value=FULL_METADATA,
        ), patch("app.schedulers.generate_scheduler.settings") as mock_settings:
            mock_settings.campaigns_dir = str(tmp_path)
            mock_settings.companies_dir = str(tmp_path / "companies")
            result = _process_campaign(
                storage,
                planner,
                caption_gen,
                prompt_gen,
                image_service,
                branding_service,
                COMPANY,
                EVENT,
            )
        assert result is True
        caption_gen.generate.assert_not_called()
        storage.save_metadata.assert_not_called()

    def test_reuses_existing_campaign_id_on_resume(self, tmp_path, services):
        storage, planner, caption_gen, prompt_gen, image_service, branding_service = (
            services
        )
        partial = {**FULL_METADATA, "caption": "", "status": "partial"}
        with patch(
            "app.schedulers.generate_scheduler._load_existing_metadata",
            return_value=partial,
        ), patch("app.schedulers.generate_scheduler.settings") as mock_settings:
            mock_settings.campaigns_dir = str(tmp_path)
            mock_settings.companies_dir = str(tmp_path / "companies")
            _process_campaign(
                storage,
                planner,
                caption_gen,
                prompt_gen,
                image_service,
                branding_service,
                COMPANY,
                EVENT,
            )
        saved_id = storage.save_metadata.call_args[0][0]
        assert saved_id == partial["id"]

    def test_only_reruns_missing_caption(self, tmp_path, services):
        storage, planner, caption_gen, prompt_gen, image_service, branding_service = (
            services
        )
        image_file = tmp_path / "image.png"
        image_file.write_bytes(b"PNG")
        partial = {
            **FULL_METADATA,
            "caption": "",
            "image_path": str(image_file),
            "status": "partial",
        }
        with patch(
            "app.schedulers.generate_scheduler._load_existing_metadata",
            return_value=partial,
        ), patch("app.schedulers.generate_scheduler.settings") as mock_settings:
            mock_settings.campaigns_dir = str(tmp_path)
            mock_settings.companies_dir = str(tmp_path / "companies")
            _process_campaign(
                storage,
                planner,
                caption_gen,
                prompt_gen,
                image_service,
                branding_service,
                COMPANY,
                EVENT,
            )
        caption_gen.generate.assert_called_once()
        prompt_gen.generate.assert_not_called()
        image_service.generate.assert_not_called()

    def test_preserves_generated_at_on_resume(self, tmp_path, services):
        storage, planner, caption_gen, prompt_gen, image_service, branding_service = (
            services
        )
        partial = {**FULL_METADATA, "caption": "", "status": "partial"}
        with patch(
            "app.schedulers.generate_scheduler._load_existing_metadata",
            return_value=partial,
        ), patch("app.schedulers.generate_scheduler.settings") as mock_settings:
            mock_settings.campaigns_dir = str(tmp_path)
            mock_settings.companies_dir = str(tmp_path / "companies")
            _process_campaign(
                storage,
                planner,
                caption_gen,
                prompt_gen,
                image_service,
                branding_service,
                COMPANY,
                EVENT,
            )
        saved = storage.save_metadata.call_args[0][1]
        assert saved["generated_at"] == partial["generated_at"]


class TestProcessCampaignIrrelevant:
    def test_returns_true_when_event_not_relevant(self, tmp_path, services):
        storage, planner, caption_gen, prompt_gen, image_service, branding_service = (
            services
        )
        planner.plan.return_value = None
        with patch(
            "app.schedulers.generate_scheduler._load_existing_metadata",
            return_value=None,
        ), patch("app.schedulers.generate_scheduler.settings") as mock_settings:
            mock_settings.campaigns_dir = str(tmp_path)
            mock_settings.companies_dir = str(tmp_path / "companies")
            result = _process_campaign(
                storage,
                planner,
                caption_gen,
                prompt_gen,
                image_service,
                branding_service,
                COMPANY,
                EVENT,
            )
        assert result is True
        storage.save_metadata.assert_not_called()
