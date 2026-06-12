"""Protocol definition for text generation providers."""

from typing import Protocol

from .models import TextGenerationRequest, TextGenerationResponse


class TextGenerationProvider(Protocol):
    """Protocol for AI text generation providers.

    This protocol defines the interface that all text generation providers
    must implement. It uses structural subtyping (duck typing) for
    type-safe provider implementations.
    """

    def generate(self, request: TextGenerationRequest) -> TextGenerationResponse:
        """Generate text based on the provided request.

        Args:
            request: The text generation request containing messages
                and parameters

        Returns:
            TextGenerationResponse containing the generated text and
                metadata

        Raises:
            Exception: Provider-specific errors during generation
        """
        ...
