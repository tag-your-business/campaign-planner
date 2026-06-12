"""Unit tests for AnthropicProvider."""

from unittest.mock import MagicMock, patch

import pytest
from app.common.ai_providers import Message, TextGenerationRequest
from app.common.ai_providers.providers import AnthropicProvider


class TestAnthropicProvider:
    """Tests for Anthropic provider."""

    def test_initialization(self):
        """Test provider initialization."""
        provider = AnthropicProvider(api_key="sk-ant-test123", model="claude-opus-4-8")

        assert provider.api_key == "sk-ant-test123"
        assert provider.model == "claude-opus-4-8"
        assert provider.client is not None

    @patch("app.common.ai_providers.providers.anthropic_provider.Anthropic")
    def test_generate_success(self, mock_anthropic_class):
        """Test successful text generation."""
        # Setup mock
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Generated response"
        mock_response.usage.input_tokens = 40
        mock_response.usage.output_tokens = 25

        mock_client.messages.create.return_value = mock_response

        # Create provider and request
        provider = AnthropicProvider(api_key="sk-ant-test123", model="claude-opus-4-8")
        request = TextGenerationRequest(
            messages=[
                Message(role="system", content="You are helpful."),
                Message(role="user", content="Hello!"),
            ],
            temperature=0.7,
            max_tokens=200,
        )

        # Generate
        response = provider.generate(request)

        # Assert
        assert response.text == "Generated response"
        assert response.provider == "anthropic"
        assert response.model == "claude-opus-4-8"
        assert response.usage["prompt_tokens"] == 40
        assert response.usage["completion_tokens"] == 25
        assert response.usage["total_tokens"] == 65

        # Verify API call
        mock_client.messages.create.assert_called_once()
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-opus-4-8"
        assert call_kwargs["max_tokens"] == 200
        assert call_kwargs["system"] == "You are helpful."
        assert len(call_kwargs["messages"]) == 1
        assert call_kwargs["messages"][0]["role"] == "user"

    @patch("app.common.ai_providers.providers.anthropic_provider.Anthropic")
    def test_system_prompt_separation(self, mock_anthropic_class):
        """Test that system prompts are separated from messages."""
        # Setup mock
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Response"
        mock_response.usage = None

        mock_client.messages.create.return_value = mock_response

        # Create provider
        provider = AnthropicProvider(api_key="sk-ant-test123", model="claude-opus-4-8")

        # Request with system and user messages
        request = TextGenerationRequest(
            messages=[
                Message(role="system", content="System instruction"),
                Message(role="user", content="User query"),
                Message(role="assistant", content="Assistant reply"),
                Message(role="user", content="Follow-up"),
            ]
        )

        provider.generate(request)

        # System should be separate, only non-system in messages
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["system"] == "System instruction"
        assert len(call_kwargs["messages"]) == 3
        assert call_kwargs["messages"][0]["role"] == "user"
        assert call_kwargs["messages"][1]["role"] == "assistant"
        assert call_kwargs["messages"][2]["role"] == "user"

    @patch("app.common.ai_providers.providers.anthropic_provider.Anthropic")
    def test_generate_without_system_prompt(self, mock_anthropic_class):
        """Test generation without system prompt."""
        # Setup mock
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Response"
        mock_response.usage = None

        mock_client.messages.create.return_value = mock_response

        # Create provider
        provider = AnthropicProvider(api_key="sk-ant-test123", model="claude-opus-4-8")

        # Request without system message
        request = TextGenerationRequest(
            messages=[Message(role="user", content="Hello")]
        )

        provider.generate(request)

        # System should not be in call
        call_kwargs = mock_client.messages.create.call_args[1]
        assert "system" not in call_kwargs or call_kwargs["system"] is None

    @patch("app.common.ai_providers.providers.anthropic_provider.Anthropic")
    def test_generate_with_model_override(self, mock_anthropic_class):
        """Test generation with model override in request."""
        # Setup mock
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Response"
        mock_response.usage = None

        mock_client.messages.create.return_value = mock_response

        # Create provider with default model
        provider = AnthropicProvider(api_key="sk-ant-test123", model="claude-opus-4-8")

        # Request with different model
        request = TextGenerationRequest(
            messages=[Message(role="user", content="Test")],
            model="claude-sonnet-4-5",
        )

        response = provider.generate(request)

        # Should use request model
        assert response.model == "claude-sonnet-4-5"
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["model"] == "claude-sonnet-4-5"

    @patch("app.common.ai_providers.providers.anthropic_provider.Anthropic")
    def test_temperature_handling(self, mock_anthropic_class):
        """Test temperature parameter handling."""
        # Setup mock
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Response"
        mock_response.usage = None

        mock_client.messages.create.return_value = mock_response

        provider = AnthropicProvider(api_key="sk-ant-test123", model="claude-opus-4-8")

        # Test with non-default temperature
        request1 = TextGenerationRequest(
            messages=[Message(role="user", content="Test")],
            temperature=0.9,
        )
        provider.generate(request1)
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["temperature"] == 0.9

        # Test with default temperature (0.7) - should not be included
        request2 = TextGenerationRequest(
            messages=[Message(role="user", content="Test")],
            temperature=0.7,
        )
        provider.generate(request2)
        call_kwargs = mock_client.messages.create.call_args[1]
        assert "temperature" not in call_kwargs

    @patch("app.common.ai_providers.providers.anthropic_provider.Anthropic")
    def test_generate_with_extra_params(self, mock_anthropic_class):
        """Test generation with extra parameters."""
        # Setup mock
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Response"
        mock_response.usage = None

        mock_client.messages.create.return_value = mock_response

        provider = AnthropicProvider(api_key="sk-ant-test123", model="claude-opus-4-8")

        # Request with extra params
        request = TextGenerationRequest(
            messages=[Message(role="user", content="Test")],
            extra_params={"top_p": 0.95, "top_k": 40},
        )

        provider.generate(request)

        # Extra params should be passed through
        call_kwargs = mock_client.messages.create.call_args[1]
        assert call_kwargs["top_p"] == 0.95
        assert call_kwargs["top_k"] == 40

    @patch("app.common.ai_providers.providers.anthropic_provider.Anthropic")
    def test_generate_api_error(self, mock_anthropic_class):
        """Test handling of API errors."""
        # Setup mock to raise error
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API Error")

        provider = AnthropicProvider(api_key="sk-ant-test123", model="claude-opus-4-8")
        request = TextGenerationRequest(messages=[Message(role="user", content="Test")])

        # Should propagate exception
        with pytest.raises(Exception, match="API Error"):
            provider.generate(request)

    @patch("app.common.ai_providers.providers.anthropic_provider.Anthropic")
    def test_usage_information_none(self, mock_anthropic_class):
        """Test handling when usage information is not available."""
        # Setup mock without usage info
        mock_client = MagicMock()
        mock_anthropic_class.return_value = mock_client

        mock_response = MagicMock()
        mock_response.content = [MagicMock()]
        mock_response.content[0].text = "Response"
        mock_response.usage = None

        mock_client.messages.create.return_value = mock_response

        provider = AnthropicProvider(api_key="sk-ant-test123", model="claude-opus-4-8")
        request = TextGenerationRequest(messages=[Message(role="user", content="Test")])

        response = provider.generate(request)

        # Usage should be None
        assert response.usage is None
