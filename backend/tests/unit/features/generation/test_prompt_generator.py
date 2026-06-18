"""Unit tests for PromptGenerator — provider is mocked via ProviderFactory."""

from unittest.mock import MagicMock, patch

import pytest
from app.common.ai_providers import TextGenerationRequest
from app.features.generation.prompt import PromptGenerator

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

DENTAL_SPEC = {
    "event_name": "World Oral Health Day",
    "company_name": "Smile Dental Clinic",
    "industry": "dental",
    "tone": "professional",
    "brand_colors": ["#FFFFFF", "#0066CC"],
    "event_tags": ["health", "oral", "dental"],
}

RESTAURANT_SPEC = {
    "event_name": "Thanksgiving",
    "company_name": "Happy Kitchen",
    "industry": "restaurant",
    "tone": "friendly",
    "brand_colors": [],
}

MINIMAL_SPEC = {
    "event_name": "New Year",
}


def _make_provider_response(text: str) -> MagicMock:
    """Build a minimal TextGenerationResponse mock."""
    resp = MagicMock()
    resp.text = text
    resp.provider = "openai"
    resp.model = "gpt-5.4-mini"
    return resp


@pytest.fixture
def mock_provider():
    """Replace ProviderFactory.create with a mock provider for each test."""
    with patch("app.features.generation.prompt.ProviderFactory") as MockFactory:
        provider = MagicMock()
        MockFactory.create.return_value = provider
        provider.generate.return_value = _make_provider_response(
            "A vibrant dental care image celebrating World Oral Health Day"
        )
        yield provider


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------


class TestPromptGeneratorSuccess:
    def test_generate_returns_string(self, mock_provider):
        gen = PromptGenerator()
        result = gen.generate(DENTAL_SPEC)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_returns_provider_text(self, mock_provider):
        expected = "Photorealistic dental clinic scene with bright smiles"
        mock_provider.generate.return_value = _make_provider_response(expected)
        gen = PromptGenerator()
        assert gen.generate(DENTAL_SPEC) == expected

    def test_generate_strips_surrounding_whitespace(self, mock_provider):
        mock_provider.generate.return_value = _make_provider_response(
            "  A bright dental image  \n"
        )
        gen = PromptGenerator()
        assert gen.generate(DENTAL_SPEC) == "A bright dental image"

    def test_generate_calls_provider_once(self, mock_provider):
        gen = PromptGenerator()
        gen.generate(DENTAL_SPEC)
        mock_provider.generate.assert_called_once()

    def test_generate_without_brand_colors(self, mock_provider):
        mock_provider.generate.return_value = _make_provider_response("Colorful image")
        gen = PromptGenerator()
        result = gen.generate(RESTAURANT_SPEC)
        assert result == "Colorful image"

    def test_generate_with_minimal_spec(self, mock_provider):
        mock_provider.generate.return_value = _make_provider_response(
            "Generic event image"
        )
        gen = PromptGenerator()
        result = gen.generate(MINIMAL_SPEC)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# Request payload verification
# ---------------------------------------------------------------------------


class TestPromptGeneratorPayload:
    def _get_request(self, mock_provider, spec: dict) -> TextGenerationRequest:
        gen = PromptGenerator()
        gen.generate(spec)
        return mock_provider.generate.call_args[0][0]

    def test_passes_system_message(self, mock_provider):
        req = self._get_request(mock_provider, DENTAL_SPEC)
        assert req.messages[0].role == "system"
        assert len(req.messages[0].content) > 0

    def test_passes_user_message(self, mock_provider):
        req = self._get_request(mock_provider, DENTAL_SPEC)
        assert req.messages[1].role == "user"

    def test_event_name_in_user_message(self, mock_provider):
        req = self._get_request(mock_provider, DENTAL_SPEC)
        assert "World Oral Health Day" in req.messages[1].content

    def test_industry_in_user_message(self, mock_provider):
        req = self._get_request(mock_provider, DENTAL_SPEC)
        assert "dental" in req.messages[1].content

    def test_brand_colors_in_user_message(self, mock_provider):
        req = self._get_request(mock_provider, DENTAL_SPEC)
        assert any(c in req.messages[1].content for c in DENTAL_SPEC["brand_colors"])

    def test_tone_in_user_message(self, mock_provider):
        req = self._get_request(mock_provider, DENTAL_SPEC)
        assert "professional" in req.messages[1].content

    def test_missing_brand_colors_falls_back_gracefully(self, mock_provider):
        req = self._get_request(mock_provider, RESTAURANT_SPEC)
        assert "color" in req.messages[1].content.lower()


# ---------------------------------------------------------------------------
# Error-handling tests
# ---------------------------------------------------------------------------


class TestPromptGeneratorErrors:
    def test_raises_on_provider_error(self, mock_provider):
        mock_provider.generate.side_effect = Exception("Provider unavailable")
        gen = PromptGenerator()
        with pytest.raises(Exception, match="Provider unavailable"):
            gen.generate(DENTAL_SPEC)
