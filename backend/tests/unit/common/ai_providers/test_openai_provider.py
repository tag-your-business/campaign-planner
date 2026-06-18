"""Unit tests for OpenAIProvider."""

from unittest.mock import MagicMock, patch

import pytest
from app.common.ai_providers import Message, TextGenerationRequest
from app.common.ai_providers.providers import OpenAIProvider


class TestOpenAIProvider:
    """Tests for OpenAI provider."""

    def test_initialization(self):
        """Test provider initialization."""
        provider = OpenAIProvider(api_key="sk-test123", model="gpt-5.4-mini")

        assert provider.api_key == "sk-test123"
        assert provider.model == "gpt-5.4-mini"
        assert provider.client is not None

    @patch("app.common.ai_providers.providers.openai_provider.OpenAI")
    def test_generate_success(self, mock_openai_class):
        """Test successful text generation."""
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Generated caption"
        mock_response.usage.prompt_tokens = 50
        mock_response.usage.completion_tokens = 20
        mock_response.usage.total_tokens = 70

        mock_client.chat.completions.create.return_value = mock_response

        # Create provider and request
        provider = OpenAIProvider(api_key="sk-test123", model="gpt-5.4-mini")
        request = TextGenerationRequest(
            messages=[
                Message(role="system", content="You are helpful."),
                Message(role="user", content="Hello!"),
            ],
            temperature=0.7,
            max_tokens=100,
        )

        # Generate
        response = provider.generate(request)

        # Assert
        assert response.text == "Generated caption"
        assert response.provider == "openai"
        assert response.model == "gpt-5.4-mini"
        assert response.usage["prompt_tokens"] == 50
        assert response.usage["completion_tokens"] == 20
        assert response.usage["total_tokens"] == 70

        # Verify API call
        mock_client.chat.completions.create.assert_called_once()
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "gpt-5.4-mini"
        assert call_kwargs["temperature"] == 0.7
        assert call_kwargs["max_completion_tokens"] == 100
        assert len(call_kwargs["messages"]) == 2

    @patch("app.common.ai_providers.providers.openai_provider.OpenAI")
    def test_generate_with_model_override(self, mock_openai_class):
        """Test generation with model override in request."""
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.usage = None

        mock_client.chat.completions.create.return_value = mock_response

        # Create provider with default model
        provider = OpenAIProvider(api_key="sk-test123", model="gpt-5.4-mini")

        # Request with different model
        request = TextGenerationRequest(
            messages=[Message(role="user", content="Test")],
            model="gpt-5.4",
        )

        response = provider.generate(request)

        # Should use request model, not provider default
        assert response.model == "gpt-5.4"
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["model"] == "gpt-5.4"

    @patch("app.common.ai_providers.providers.openai_provider.OpenAI")
    def test_generate_with_extra_params(self, mock_openai_class):
        """Test generation with extra parameters."""
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.usage = None

        mock_client.chat.completions.create.return_value = mock_response

        # Create provider
        provider = OpenAIProvider(api_key="sk-test123", model="gpt-5.4-mini")

        # Request with extra params
        request = TextGenerationRequest(
            messages=[Message(role="user", content="Test")],
            extra_params={"top_p": 0.9, "presence_penalty": 0.5},
        )

        provider.generate(request)

        # Extra params should be passed through
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        assert call_kwargs["top_p"] == 0.9
        assert call_kwargs["presence_penalty"] == 0.5

    @patch("app.common.ai_providers.providers.openai_provider.OpenAI")
    def test_generate_api_error(self, mock_openai_class):
        """Test handling of API errors."""
        # Setup mock to raise error
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client
        mock_client.chat.completions.create.side_effect = Exception("API Error")

        provider = OpenAIProvider(api_key="sk-test123", model="gpt-5.4-mini")
        request = TextGenerationRequest(messages=[Message(role="user", content="Test")])

        # Should propagate exception
        with pytest.raises(Exception, match="API Error"):
            provider.generate(request)

    @patch("app.common.ai_providers.providers.openai_provider.OpenAI")
    def test_message_format_conversion(self, mock_openai_class):
        """Test Message dataclass conversion to OpenAI format."""
        # Setup mock
        mock_client = MagicMock()
        mock_openai_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Response"
        mock_response.usage = None

        mock_client.chat.completions.create.return_value = mock_response

        # Create provider
        provider = OpenAIProvider(api_key="sk-test123", model="gpt-5.4-mini")

        # Request with multiple message types
        request = TextGenerationRequest(
            messages=[
                Message(role="system", content="System prompt"),
                Message(role="user", content="User message"),
                Message(role="assistant", content="Assistant message"),
                Message(role="user", content="Follow-up"),
            ]
        )

        provider.generate(request)

        # Check message conversion
        call_kwargs = mock_client.chat.completions.create.call_args[1]
        messages = call_kwargs["messages"]

        assert len(messages) == 4
        assert messages[0] == {"role": "system", "content": "System prompt"}
        assert messages[1] == {"role": "user", "content": "User message"}
        assert messages[2] == {
            "role": "assistant",
            "content": "Assistant message",
        }
        assert messages[3] == {"role": "user", "content": "Follow-up"}
