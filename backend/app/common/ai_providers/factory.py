"""Factory for creating AI text generation providers."""

import logging

from app.core.config import settings

from .protocol import TextGenerationProvider
from .providers.anthropic_provider import AnthropicProvider
from .providers.nvidia_provider import NvidiaProvider
from .providers.openai_provider import OpenAIProvider

logger = logging.getLogger(__name__)


class ProviderFactory:
    """Factory for instantiating text generation providers.

    Creates provider instances based on configuration settings.
    Validates API keys and provides clear error messages.
    """

    @staticmethod
    def create(provider_name: str | None = None) -> TextGenerationProvider:
        """Create a text generation provider instance.

        Args:
            provider_name: Optional provider name override
                ('openai', 'nvidia', 'anthropic').
                If None, uses TEXT_GENERATION_PROVIDER from settings.

        Returns:
            TextGenerationProvider instance ready for use

        Raises:
            ValueError: If provider name is invalid or API key is missing
        """
        # Use provided name or default from settings
        name = provider_name or settings.text_generation_provider
        name = name.lower().strip()

        logger.debug(f"Creating text generation provider: {name}")

        # Create provider based on name
        if name == "openai":
            return ProviderFactory._create_openai()
        elif name == "nvidia":
            return ProviderFactory._create_nvidia()
        elif name == "anthropic":
            return ProviderFactory._create_anthropic()
        else:
            raise ValueError(
                f"Unsupported text generation provider: {name}. "
                f"Supported providers: openai, nvidia, anthropic"
            )

    @staticmethod
    def _create_openai() -> OpenAIProvider:
        """Create OpenAI provider instance.

        Returns:
            Configured OpenAIProvider

        Raises:
            ValueError: If API key is missing
        """
        if not settings.openai_api_key:
            raise ValueError(
                "OpenAI API key not configured. "
                "Set OPENAI_API_KEY environment variable."
            )

        return OpenAIProvider(
            api_key=settings.openai_api_key,
            model=settings.openai_text_model,
        )

    @staticmethod
    def _create_nvidia() -> NvidiaProvider:
        """Create NVIDIA provider instance.

        Returns:
            Configured NvidiaProvider

        Raises:
            ValueError: If API key is missing
        """
        if not settings.nvidia_api_key:
            raise ValueError(
                "NVIDIA API key not configured. "
                "Set NVIDIA_API_KEY environment variable."
            )

        return NvidiaProvider(
            api_key=settings.nvidia_api_key,
            model=settings.nvidia_text_model,
        )

    @staticmethod
    def _create_anthropic() -> AnthropicProvider:
        """Create Anthropic provider instance.

        Returns:
            Configured AnthropicProvider

        Raises:
            ValueError: If API key is missing
        """
        if not settings.anthropic_api_key:
            raise ValueError(
                "Anthropic API key not configured. "
                "Set ANTHROPIC_API_KEY environment variable."
            )

        return AnthropicProvider(
            api_key=settings.anthropic_api_key,
            model=settings.anthropic_text_model,
        )
