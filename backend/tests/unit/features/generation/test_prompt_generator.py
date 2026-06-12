"""Unit tests for PromptGenerator — all Anthropic API calls are mocked."""

from unittest.mock import MagicMock, patch

import pytest
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


def _make_claude_response(text: str) -> MagicMock:
    """Build a minimal Anthropic messages.create response mock."""
    return MagicMock(content=[MagicMock(text=text)])


@pytest.fixture
def mock_anthropic():
    """Replace the Anthropic client with a mock for the duration of each test."""
    with patch("app.features.generation.prompt.Anthropic") as MockCls:
        client = MagicMock()
        MockCls.return_value = client
        client.messages.create.return_value = _make_claude_response(
            "A vibrant dental care image celebrating World Oral Health Day"
        )
        yield client


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------


class TestPromptGeneratorSuccess:
    def test_generate_returns_string(self, mock_anthropic):
        gen = PromptGenerator()
        result = gen.generate(DENTAL_SPEC)
        assert isinstance(result, str)
        assert len(result) > 0

    def test_generate_returns_claude_text(self, mock_anthropic):
        expected = "Photorealistic dental clinic scene with bright smiles"
        mock_anthropic.messages.create.return_value = _make_claude_response(expected)
        gen = PromptGenerator()
        assert gen.generate(DENTAL_SPEC) == expected

    def test_generate_strips_surrounding_whitespace(self, mock_anthropic):
        mock_anthropic.messages.create.return_value = _make_claude_response(
            "  A bright dental image  \n"
        )
        gen = PromptGenerator()
        assert gen.generate(DENTAL_SPEC) == "A bright dental image"

    def test_generate_calls_claude_once(self, mock_anthropic):
        gen = PromptGenerator()
        gen.generate(DENTAL_SPEC)
        mock_anthropic.messages.create.assert_called_once()

    def test_generate_without_brand_colors(self, mock_anthropic):
        mock_anthropic.messages.create.return_value = _make_claude_response(
            "Colorful image"
        )
        gen = PromptGenerator()
        result = gen.generate(RESTAURANT_SPEC)
        assert result == "Colorful image"

    def test_generate_with_minimal_spec(self, mock_anthropic):
        mock_anthropic.messages.create.return_value = _make_claude_response(
            "Generic event image"
        )
        gen = PromptGenerator()
        result = gen.generate(MINIMAL_SPEC)
        assert isinstance(result, str)


# ---------------------------------------------------------------------------
# API call content verification
# ---------------------------------------------------------------------------


class TestPromptGeneratorApiPayload:
    def test_passes_model_to_claude(self, mock_anthropic):
        gen = PromptGenerator()
        gen.generate(DENTAL_SPEC)
        kwargs = mock_anthropic.messages.create.call_args.kwargs
        assert "model" in kwargs
        assert isinstance(kwargs["model"], str)
        assert len(kwargs["model"]) > 0

    def test_passes_system_prompt(self, mock_anthropic):
        gen = PromptGenerator()
        gen.generate(DENTAL_SPEC)
        kwargs = mock_anthropic.messages.create.call_args.kwargs
        assert "system" in kwargs
        assert len(kwargs["system"]) > 0

    def test_event_name_in_user_message(self, mock_anthropic):
        gen = PromptGenerator()
        gen.generate(DENTAL_SPEC)
        kwargs = mock_anthropic.messages.create.call_args.kwargs
        user_content = kwargs["messages"][0]["content"]
        assert "World Oral Health Day" in user_content

    def test_industry_in_user_message(self, mock_anthropic):
        gen = PromptGenerator()
        gen.generate(DENTAL_SPEC)
        kwargs = mock_anthropic.messages.create.call_args.kwargs
        user_content = kwargs["messages"][0]["content"]
        assert "dental" in user_content

    def test_brand_colors_in_user_message(self, mock_anthropic):
        gen = PromptGenerator()
        gen.generate(DENTAL_SPEC)
        kwargs = mock_anthropic.messages.create.call_args.kwargs
        user_content = kwargs["messages"][0]["content"]
        # At least one brand color should appear
        assert any(c in user_content for c in DENTAL_SPEC["brand_colors"])

    def test_tone_in_user_message(self, mock_anthropic):
        gen = PromptGenerator()
        gen.generate(DENTAL_SPEC)
        kwargs = mock_anthropic.messages.create.call_args.kwargs
        user_content = kwargs["messages"][0]["content"]
        assert "professional" in user_content

    def test_user_message_role_is_user(self, mock_anthropic):
        gen = PromptGenerator()
        gen.generate(DENTAL_SPEC)
        kwargs = mock_anthropic.messages.create.call_args.kwargs
        assert kwargs["messages"][0]["role"] == "user"

    def test_missing_brand_colors_falls_back_gracefully(self, mock_anthropic):
        gen = PromptGenerator()
        gen.generate(RESTAURANT_SPEC)
        kwargs = mock_anthropic.messages.create.call_args.kwargs
        user_content = kwargs["messages"][0]["content"]
        # Should still have some color descriptor
        assert "color" in user_content.lower()


# ---------------------------------------------------------------------------
# Error-handling / retry tests
# ---------------------------------------------------------------------------


class TestPromptGeneratorRetry:
    def test_raises_immediately_on_persistent_error(self, mock_anthropic):
        mock_anthropic.messages.create.side_effect = Exception("Claude unavailable")
        gen = PromptGenerator()
        with pytest.raises(Exception, match="Claude unavailable"):
            gen.generate(DENTAL_SPEC)

    def test_exhausts_all_three_attempts(self, mock_anthropic):
        mock_anthropic.messages.create.side_effect = Exception("API down")
        gen = PromptGenerator()
        with pytest.raises(Exception):
            gen.generate(DENTAL_SPEC)
        assert mock_anthropic.messages.create.call_count == 3

    def test_succeeds_on_second_attempt(self, mock_anthropic):
        mock_anthropic.messages.create.side_effect = [
            Exception("Transient failure"),
            _make_claude_response("Recovered prompt"),
        ]
        gen = PromptGenerator()
        result = gen.generate(DENTAL_SPEC)
        assert result == "Recovered prompt"
        assert mock_anthropic.messages.create.call_count == 2

    def test_succeeds_on_third_attempt(self, mock_anthropic):
        mock_anthropic.messages.create.side_effect = [
            Exception("Error 1"),
            Exception("Error 2"),
            _make_claude_response("Third-try prompt"),
        ]
        gen = PromptGenerator()
        result = gen.generate(DENTAL_SPEC)
        assert result == "Third-try prompt"
        assert mock_anthropic.messages.create.call_count == 3
