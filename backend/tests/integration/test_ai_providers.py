"""Integration tests for AI provider abstraction."""

from unittest.mock import patch

import pytest
from app.common.ai_providers import Message, ProviderFactory, TextGenerationRequest
from app.features.generation.caption import CaptionGenerator


class TestAIProviderIntegration:
    """Integration tests for AI provider abstraction."""

    @patch("app.common.ai_providers.factory.settings")
    @patch("app.common.ai_providers.providers.openai_provider.OpenAI")
    def test_caption_generation_with_openai(self, mock_openai_class, mock_settings):
        """Test caption generation using OpenAI provider."""
        # Setup mock settings
        mock_settings.text_generation_provider = "openai"
        mock_settings.openai_api_key = "sk-test123"
        mock_settings.openai_text_model = "gpt-4o-mini"

        # Setup mock OpenAI client
        mock_client = mock_openai_class.return_value
        mock_response = type(
            "Response",
            (),
            {
                "choices": [
                    type(
                        "Choice",
                        (),
                        {"message": type("Message", (), {"content": "Test caption"})()},
                    )()
                ],
                "usage": type(
                    "Usage",
                    (),
                    {
                        "prompt_tokens": 10,
                        "completion_tokens": 5,
                        "total_tokens": 15,
                    },
                )(),
            },
        )()
        mock_client.chat.completions.create.return_value = mock_response

        # Create caption generator
        caption_gen = CaptionGenerator()

        # Generate caption
        campaign_spec = {
            "event_name": "New Year's Day",
            "company_name": "Test Company",
            "industry": "Technology",
            "tone": "Professional",
            "event_tags": ["celebration", "newyear"],
        }

        caption = caption_gen.generate(campaign_spec)

        # Verify
        assert caption == "Test caption"
        assert mock_client.chat.completions.create.called

    @patch("app.common.ai_providers.factory.settings")
    @patch("app.common.ai_providers.providers.nvidia_provider.OpenAI")
    def test_caption_generation_with_nvidia(self, mock_openai_class, mock_settings):
        """Test caption generation using NVIDIA provider."""
        from tests.mocks.mock_openai_client import MockOpenAIClient

        # Setup mock settings
        mock_settings.text_generation_provider = "nvidia"
        mock_settings.nvidia_api_key = "nvapi-test123"
        mock_settings.nvidia_text_model = "meta/llama-3.1-8b-instruct"

        # Setup mock OpenAI-compatible client (NVIDIA uses the OpenAI SDK)
        mock_client = MockOpenAIClient(custom_caption="NVIDIA generated caption")
        mock_openai_class.return_value = mock_client

        # Create caption generator with NVIDIA provider
        caption_gen = CaptionGenerator()

        # Generate caption
        campaign_spec = {
            "event_name": "Valentine's Day",
            "company_name": "Test Company",
            "industry": "Retail",
            "tone": "Friendly",
            "event_tags": ["love", "valentine"],
        }

        caption = caption_gen.generate(campaign_spec)

        # Verify
        assert caption == "NVIDIA generated caption"
        assert mock_openai_class.called

    @patch("app.common.ai_providers.factory.settings")
    @patch("app.common.ai_providers.providers.anthropic_provider.Anthropic")
    def test_caption_generation_with_anthropic(
        self, mock_anthropic_class, mock_settings
    ):
        """Test caption generation using Anthropic provider."""
        # Setup mock settings
        mock_settings.text_generation_provider = "anthropic"
        mock_settings.anthropic_api_key = "sk-ant-test123"
        mock_settings.anthropic_text_model = "claude-opus-4-8"

        # Setup mock Anthropic client
        mock_client = mock_anthropic_class.return_value
        mock_response = type(
            "Response",
            (),
            {
                "content": [type("Content", (), {"text": "Anthropic caption"})()],
                "usage": type("Usage", (), {"input_tokens": 10, "output_tokens": 5})(),
            },
        )()
        mock_client.messages.create.return_value = mock_response

        # Create caption generator
        caption_gen = CaptionGenerator()

        # Generate caption
        campaign_spec = {
            "event_name": "Earth Day",
            "company_name": "Test Company",
            "industry": "Environmental",
            "tone": "Inspirational",
            "event_tags": ["environment", "sustainability"],
        }

        caption = caption_gen.generate(campaign_spec)

        # Verify
        assert caption == "Anthropic caption"
        assert mock_client.messages.create.called

    @patch("app.common.ai_providers.factory.settings")
    def test_provider_switching_via_constructor(self, mock_settings):
        """Test that provider can be overridden via constructor."""
        # Setup mock settings with OpenAI as default
        mock_settings.text_generation_provider = "openai"
        mock_settings.nvidia_api_key = "nvapi-test123"
        mock_settings.nvidia_text_model = "meta/llama-3.1-8b-instruct"

        # Create generator with explicit NVIDIA override
        caption_gen = CaptionGenerator(provider_name="nvidia")

        # Verify provider type
        from app.common.ai_providers.providers import NvidiaProvider

        assert isinstance(caption_gen.provider, NvidiaProvider)

    @patch("app.common.ai_providers.factory.settings")
    def test_backward_compatibility_default_openai(self, mock_settings):
        """Test backward compatibility - defaults to OpenAI."""
        # Setup settings with OpenAI key
        mock_settings.text_generation_provider = "openai"
        mock_settings.openai_api_key = "sk-test123"
        mock_settings.openai_text_model = "gpt-4o-mini"

        # Create caption generator (should use OpenAI by default)
        caption_gen = CaptionGenerator()

        # Verify it's using OpenAI provider
        from app.common.ai_providers.providers import OpenAIProvider

        assert isinstance(caption_gen.provider, OpenAIProvider)

    def test_direct_provider_usage(self):
        """Test using provider directly without caption generator."""
        # Create a mock provider
        from tests.mocks.mock_provider import MockProvider

        provider = MockProvider(response_text="Direct provider test")

        # Create request
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

        # Verify
        assert response.text == "Direct provider test"
        assert response.provider == "mock"
        assert provider.call_count == 1
        assert provider.last_request == request

    @patch("app.common.ai_providers.factory.settings")
    def test_factory_error_handling(self, mock_settings):
        """Test factory error handling for invalid configurations."""
        # Test unsupported provider
        mock_settings.text_generation_provider = "unsupported"

        with pytest.raises(ValueError, match="Unsupported text generation"):
            ProviderFactory.create()

        # Test missing API key
        mock_settings.text_generation_provider = "openai"
        mock_settings.openai_api_key = ""

        with pytest.raises(ValueError, match="OpenAI API key not configured"):
            ProviderFactory.create()
