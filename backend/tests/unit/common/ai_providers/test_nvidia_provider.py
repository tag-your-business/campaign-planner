"""Unit tests for NvidiaProvider."""

from unittest.mock import MagicMock, patch

import pytest
from app.common.ai_providers import Message, TextGenerationRequest
from app.common.ai_providers.providers import NvidiaProvider
from app.common.ai_providers.providers.nvidia_provider import NVIDIA_BASE_URL


def _make_openai_response(
    content: str | None, model: str = "meta/llama-3.1-8b-instruct"
):
    """Build a mock OpenAI-style completion response."""
    response = MagicMock()
    response.choices[0].message.content = content
    response.usage.prompt_tokens = 30
    response.usage.completion_tokens = 15
    response.usage.total_tokens = 45
    return response


class TestNvidiaProvider:
    """Tests for NVIDIA provider."""

    def test_initialization(self):
        """Test provider initialization."""
        provider = NvidiaProvider(
            api_key="nvapi-test123", model="meta/llama-3.1-8b-instruct"
        )

        assert provider.api_key == "nvapi-test123"
        assert provider.model == "meta/llama-3.1-8b-instruct"

    @patch("app.common.ai_providers.providers.nvidia_provider.OpenAI")
    def test_openai_client_configured_correctly(self, mock_openai_cls):
        """Test that the OpenAI client is configured with NVIDIA's base URL."""
        NvidiaProvider(api_key="nvapi-test123")

        mock_openai_cls.assert_called_once_with(
            base_url=NVIDIA_BASE_URL, api_key="nvapi-test123"
        )

    @patch("app.common.ai_providers.providers.nvidia_provider.OpenAI")
    def test_generate_success(self, mock_openai_cls):
        """Test successful text generation."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_openai_response(
            "Generated text"
        )

        provider = NvidiaProvider(
            api_key="nvapi-test123", model="meta/llama-3.1-8b-instruct"
        )
        request = TextGenerationRequest(
            messages=[
                Message(role="system", content="You are helpful."),
                Message(role="user", content="Hello!"),
            ],
            temperature=0.8,
            max_tokens=150,
        )

        response = provider.generate(request)

        assert response.text == "Generated text"
        assert response.provider == "nvidia"
        assert response.model == "meta/llama-3.1-8b-instruct"
        assert response.usage["prompt_tokens"] == 30
        assert response.usage["completion_tokens"] == 15
        assert response.usage["total_tokens"] == 45

    @patch("app.common.ai_providers.providers.nvidia_provider.OpenAI")
    def test_generate_with_model_override(self, mock_openai_cls):
        """Test generation with model override in request."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_openai_response(
            "Response"
        )

        provider = NvidiaProvider(
            api_key="nvapi-test123", model="meta/llama-3.1-8b-instruct"
        )
        request = TextGenerationRequest(
            messages=[Message(role="user", content="Test")],
            model="meta/llama-3.3-70b-instruct",
        )

        response = provider.generate(request)

        assert response.model == "meta/llama-3.3-70b-instruct"
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "meta/llama-3.3-70b-instruct"

    @patch("app.common.ai_providers.providers.nvidia_provider.OpenAI")
    def test_nvidia_specific_defaults(self, mock_openai_cls):
        """Test NVIDIA-specific default parameters are sent."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_openai_response(
            "Response"
        )

        provider = NvidiaProvider(
            api_key="nvapi-test123", model="meta/llama-3.1-8b-instruct"
        )
        request = TextGenerationRequest(messages=[Message(role="user", content="Test")])

        provider.generate(request)

        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["top_p"] == 0.7
        assert call_kwargs["stream"] is False

    @patch("app.common.ai_providers.providers.nvidia_provider.OpenAI")
    def test_generate_with_extra_params(self, mock_openai_cls):
        """Test generation with extra parameters override defaults."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_openai_response(
            "Response"
        )

        provider = NvidiaProvider(
            api_key="nvapi-test123", model="meta/llama-3.1-8b-instruct"
        )
        request = TextGenerationRequest(
            messages=[Message(role="user", content="Test")],
            extra_params={"top_p": 0.9, "frequency_penalty": 0.3},
        )

        provider.generate(request)

        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["top_p"] == 0.9
        assert call_kwargs["frequency_penalty"] == 0.3

    @patch("app.common.ai_providers.providers.nvidia_provider.OpenAI")
    def test_generate_request_error(self, mock_openai_cls):
        """Test handling of API errors."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("Network error")

        provider = NvidiaProvider(
            api_key="nvapi-test123", model="meta/llama-3.1-8b-instruct"
        )
        request = TextGenerationRequest(messages=[Message(role="user", content="Test")])

        with pytest.raises(Exception, match="Network error"):
            provider.generate(request)

    @patch("app.common.ai_providers.providers.nvidia_provider.OpenAI")
    def test_generate_none_content_raises(self, mock_openai_cls):
        """Test that None content in response raises ValueError."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_openai_response(None)

        provider = NvidiaProvider(
            api_key="nvapi-test123", model="meta/llama-3.1-8b-instruct"
        )
        request = TextGenerationRequest(messages=[Message(role="user", content="Test")])

        with pytest.raises(ValueError, match="no text content"):
            provider.generate(request)

    @patch("app.common.ai_providers.providers.nvidia_provider.OpenAI")
    def test_message_format_conversion(self, mock_openai_cls):
        """Test Message dataclass conversion to dict format."""
        mock_client = MagicMock()
        mock_openai_cls.return_value = mock_client
        mock_client.chat.completions.create.return_value = _make_openai_response(
            "Response"
        )

        provider = NvidiaProvider(
            api_key="nvapi-test123", model="meta/llama-3.1-8b-instruct"
        )
        request = TextGenerationRequest(
            messages=[
                Message(role="system", content="System prompt"),
                Message(role="user", content="User message"),
            ]
        )

        provider.generate(request)

        call_kwargs = mock_client.chat.completions.create.call_args[1]
        messages = call_kwargs["messages"]
        assert len(messages) == 2
        assert messages[0] == {"role": "system", "content": "System prompt"}
        assert messages[1] == {"role": "user", "content": "User message"}
