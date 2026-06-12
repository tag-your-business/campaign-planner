"""Unit tests for NvidiaProvider."""

from unittest.mock import MagicMock, patch

import pytest
from app.common.ai_providers import Message, TextGenerationRequest
from app.common.ai_providers.providers import NvidiaProvider


class TestNvidiaProvider:
    """Tests for NVIDIA provider."""

    def test_initialization(self):
        """Test provider initialization."""
        provider = NvidiaProvider(
            api_key="nvapi-test123", model="meta/llama-3.1-8b-instruct"
        )

        assert provider.api_key == "nvapi-test123"
        assert provider.model == "meta/llama-3.1-8b-instruct"

    @patch("app.common.ai_providers.providers.nvidia_provider.requests")
    def test_generate_success(self, mock_requests):
        """Test successful text generation."""
        # Setup mock response
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Generated text"}}],
            "usage": {
                "prompt_tokens": 30,
                "completion_tokens": 15,
                "total_tokens": 45,
            },
        }
        mock_requests.post.return_value = mock_response

        # Create provider and request
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

        # Generate
        response = provider.generate(request)

        # Assert
        assert response.text == "Generated text"
        assert response.provider == "nvidia"
        assert response.model == "meta/llama-3.1-8b-instruct"
        assert response.usage["prompt_tokens"] == 30
        assert response.usage["completion_tokens"] == 15
        assert response.usage["total_tokens"] == 45

        # Verify API call
        mock_requests.post.assert_called_once()
        call_args = mock_requests.post.call_args
        assert call_args[0][0] == NvidiaProvider.INVOKE_URL
        assert call_args[1]["headers"]["Authorization"] == ("Bearer nvapi-test123")
        assert call_args[1]["json"]["model"] == "meta/llama-3.1-8b-instruct"
        assert call_args[1]["json"]["temperature"] == 0.8
        assert call_args[1]["json"]["max_tokens"] == 150

    @patch("app.common.ai_providers.providers.nvidia_provider.requests")
    def test_generate_with_model_override(self, mock_requests):
        """Test generation with model override in request."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}]
        }
        mock_requests.post.return_value = mock_response

        # Create provider with default model
        provider = NvidiaProvider(
            api_key="nvapi-test123", model="meta/llama-3.1-8b-instruct"
        )

        # Request with different model
        request = TextGenerationRequest(
            messages=[Message(role="user", content="Test")],
            model="meta/llama-3.3-70b-instruct",
        )

        response = provider.generate(request)

        # Should use request model
        assert response.model == "meta/llama-3.3-70b-instruct"
        call_args = mock_requests.post.call_args
        assert call_args[1]["json"]["model"] == "meta/llama-3.3-70b-instruct"

    @patch("app.common.ai_providers.providers.nvidia_provider.requests")
    def test_nvidia_specific_defaults(self, mock_requests):
        """Test NVIDIA-specific default parameters."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}]
        }
        mock_requests.post.return_value = mock_response

        provider = NvidiaProvider(
            api_key="nvapi-test123", model="meta/llama-3.1-8b-instruct"
        )
        request = TextGenerationRequest(messages=[Message(role="user", content="Test")])

        provider.generate(request)

        # Check NVIDIA-specific defaults
        call_args = mock_requests.post.call_args
        payload = call_args[1]["json"]
        assert payload["top_p"] == 0.95
        assert payload["chat_template_kwargs"] == {"enable_thinking": True}
        assert payload["stream"] is False

    @patch("app.common.ai_providers.providers.nvidia_provider.requests")
    def test_generate_with_extra_params(self, mock_requests):
        """Test generation with extra parameters."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}]
        }
        mock_requests.post.return_value = mock_response

        provider = NvidiaProvider(
            api_key="nvapi-test123", model="meta/llama-3.1-8b-instruct"
        )

        # Request with extra params
        request = TextGenerationRequest(
            messages=[Message(role="user", content="Test")],
            extra_params={"top_p": 0.9, "frequency_penalty": 0.3},
        )

        provider.generate(request)

        # Extra params should override defaults
        call_args = mock_requests.post.call_args
        payload = call_args[1]["json"]
        assert payload["top_p"] == 0.9
        assert payload["frequency_penalty"] == 0.3

    @patch("app.common.ai_providers.providers.nvidia_provider.requests")
    def test_generate_request_error(self, mock_requests):
        """Test handling of request errors."""
        # Setup mock to raise error
        mock_requests.post.side_effect = Exception("Network error")

        provider = NvidiaProvider(
            api_key="nvapi-test123", model="meta/llama-3.1-8b-instruct"
        )
        request = TextGenerationRequest(messages=[Message(role="user", content="Test")])

        # Should propagate exception
        with pytest.raises(Exception, match="Network error"):
            provider.generate(request)

    @patch("app.common.ai_providers.providers.nvidia_provider.requests")
    def test_generate_invalid_response_format(self, mock_requests):
        """Test handling of invalid response format."""
        # Setup mock with invalid response
        mock_response = MagicMock()
        mock_response.json.return_value = {"invalid": "structure"}
        mock_requests.post.return_value = mock_response

        provider = NvidiaProvider(
            api_key="nvapi-test123", model="meta/llama-3.1-8b-instruct"
        )
        request = TextGenerationRequest(messages=[Message(role="user", content="Test")])

        # Should raise ValueError for invalid format
        with pytest.raises(ValueError, match="Invalid NVIDIA API response"):
            provider.generate(request)

    @patch("app.common.ai_providers.providers.nvidia_provider.requests")
    def test_message_format_conversion(self, mock_requests):
        """Test Message dataclass conversion to NVIDIA format."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}]
        }
        mock_requests.post.return_value = mock_response

        provider = NvidiaProvider(
            api_key="nvapi-test123", model="meta/llama-3.1-8b-instruct"
        )

        # Request with multiple messages
        request = TextGenerationRequest(
            messages=[
                Message(role="system", content="System prompt"),
                Message(role="user", content="User message"),
            ]
        )

        provider.generate(request)

        # Check message conversion
        call_args = mock_requests.post.call_args
        messages = call_args[1]["json"]["messages"]

        assert len(messages) == 2
        assert messages[0] == {"role": "system", "content": "System prompt"}
        assert messages[1] == {"role": "user", "content": "User message"}

    @patch("app.common.ai_providers.providers.nvidia_provider.requests")
    def test_authentication_header(self, mock_requests):
        """Test proper authentication header formatting."""
        # Setup mock
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "choices": [{"message": {"content": "Response"}}]
        }
        mock_requests.post.return_value = mock_response

        provider = NvidiaProvider(
            api_key="nvapi-test123", model="meta/llama-3.1-8b-instruct"
        )
        request = TextGenerationRequest(messages=[Message(role="user", content="Test")])

        provider.generate(request)

        # Check headers
        call_args = mock_requests.post.call_args
        headers = call_args[1]["headers"]
        assert headers["Authorization"] == "Bearer nvapi-test123"
        assert headers["Accept"] == "application/json"
        assert headers["Content-Type"] == "application/json"
