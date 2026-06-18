"""Unit tests for ProviderFactory."""

from unittest.mock import patch

import pytest
from app.common.ai_providers import ProviderFactory
from app.common.ai_providers.providers import (
    AnthropicProvider,
    NvidiaProvider,
    OpenAIProvider,
)


class TestProviderFactory:
    """Tests for ProviderFactory."""

    @patch("app.common.ai_providers.factory.settings")
    def test_create_openai_provider(self, mock_settings):
        """Test creating OpenAI provider."""
        mock_settings.text_generation_provider = "openai"
        mock_settings.openai_api_key = "sk-test123"
        mock_settings.openai_text_model = "gpt-5.4-mini"

        provider = ProviderFactory.create()

        assert isinstance(provider, OpenAIProvider)
        assert provider.api_key == "sk-test123"
        assert provider.model == "gpt-5.4-mini"

    @patch("app.common.ai_providers.factory.settings")
    def test_create_nvidia_provider(self, mock_settings):
        """Test creating NVIDIA provider."""
        mock_settings.text_generation_provider = "nvidia"
        mock_settings.nvidia_api_key = "nvapi-test123"
        mock_settings.nvidia_text_model = "meta/llama-3.1-8b-instruct"

        provider = ProviderFactory.create()

        assert isinstance(provider, NvidiaProvider)
        assert provider.api_key == "nvapi-test123"
        assert provider.model == "meta/llama-3.1-8b-instruct"

    @patch("app.common.ai_providers.factory.settings")
    def test_create_anthropic_provider(self, mock_settings):
        """Test creating Anthropic provider."""
        mock_settings.text_generation_provider = "anthropic"
        mock_settings.anthropic_api_key = "sk-ant-test123"
        mock_settings.anthropic_text_model = "claude-opus-4-8"

        provider = ProviderFactory.create()

        assert isinstance(provider, AnthropicProvider)
        assert provider.api_key == "sk-ant-test123"
        assert provider.model == "claude-opus-4-8"

    @patch("app.common.ai_providers.factory.settings")
    def test_create_with_provider_override(self, mock_settings):
        """Test creating provider with name override."""
        mock_settings.text_generation_provider = "openai"
        mock_settings.nvidia_api_key = "nvapi-test123"
        mock_settings.nvidia_text_model = "meta/llama-3.1-8b-instruct"

        # Override to nvidia even though default is openai
        provider = ProviderFactory.create(provider_name="nvidia")

        assert isinstance(provider, NvidiaProvider)

    @patch("app.common.ai_providers.factory.settings")
    def test_create_unsupported_provider(self, mock_settings):
        """Test error for unsupported provider name."""
        mock_settings.text_generation_provider = "unknown"

        with pytest.raises(ValueError, match="Unsupported text generation"):
            ProviderFactory.create()

    @patch("app.common.ai_providers.factory.settings")
    def test_create_missing_openai_key(self, mock_settings):
        """Test error when OpenAI API key is missing."""
        mock_settings.text_generation_provider = "openai"
        mock_settings.openai_api_key = ""

        with pytest.raises(ValueError, match="OpenAI API key not configured"):
            ProviderFactory.create()

    @patch("app.common.ai_providers.factory.settings")
    def test_create_missing_nvidia_key(self, mock_settings):
        """Test error when NVIDIA API key is missing."""
        mock_settings.text_generation_provider = "nvidia"
        mock_settings.nvidia_api_key = ""

        with pytest.raises(ValueError, match="NVIDIA API key not configured"):
            ProviderFactory.create()

    @patch("app.common.ai_providers.factory.settings")
    def test_create_missing_anthropic_key(self, mock_settings):
        """Test error when Anthropic API key is missing."""
        mock_settings.text_generation_provider = "anthropic"
        mock_settings.anthropic_api_key = ""

        with pytest.raises(ValueError, match="Anthropic API key not configured"):
            ProviderFactory.create()

    @patch("app.common.ai_providers.factory.settings")
    def test_provider_name_case_insensitive(self, mock_settings):
        """Test that provider names are case-insensitive."""
        mock_settings.openai_api_key = "sk-test123"
        mock_settings.openai_text_model = "gpt-5.4-mini"

        # Test uppercase
        provider1 = ProviderFactory.create(provider_name="OPENAI")
        assert isinstance(provider1, OpenAIProvider)

        # Test mixed case
        provider2 = ProviderFactory.create(provider_name="OpenAI")
        assert isinstance(provider2, OpenAIProvider)

        # Test with spaces
        provider3 = ProviderFactory.create(provider_name=" openai ")
        assert isinstance(provider3, OpenAIProvider)
