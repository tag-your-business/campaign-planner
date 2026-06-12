"""Base class for text generation providers with shared retry logic."""

from abc import ABC, abstractmethod

from tenacity import retry, stop_after_attempt, wait_exponential

from .models import TextGenerationRequest, TextGenerationResponse


class BaseTextProvider(ABC):
    """Abstract base class for text generation providers.

    Provides shared retry logic and common functionality for all providers.
    Subclasses must implement _generate_impl for provider-specific logic.
    """

    def __init__(self, api_key: str, model: str):
        """Initialize the provider with API credentials.

        Args:
            api_key: API key for the provider
            model: Default model name to use for generation
        """
        self.api_key = api_key
        self.model = model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=10),
        reraise=True,
    )
    def generate(self, request: TextGenerationRequest) -> TextGenerationResponse:
        """Generate text with automatic retry on failure.

        This method wraps _generate_impl with retry logic using exponential
        backoff. All provider-specific implementations should implement
        _generate_impl instead of overriding this method.

        Args:
            request: The text generation request

        Returns:
            TextGenerationResponse with generated text and metadata

        Raises:
            Exception: Re-raises provider-specific errors after retries
                exhausted
        """
        return self._generate_impl(request)

    @abstractmethod
    def _generate_impl(self, request: TextGenerationRequest) -> TextGenerationResponse:
        """Provider-specific implementation of text generation.

        Subclasses must implement this method to handle provider-specific
        API calls and response parsing.

        Args:
            request: The text generation request

        Returns:
            TextGenerationResponse with generated text and metadata

        Raises:
            Exception: Provider-specific errors
        """
