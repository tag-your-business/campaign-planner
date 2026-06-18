"""OpenAI text generation provider implementation."""

import logging

from openai import OpenAI

from ..base import BaseTextProvider
from ..models import TextGenerationRequest, TextGenerationResponse

logger = logging.getLogger(__name__)


class OpenAIProvider(BaseTextProvider):
    """OpenAI GPT provider for text generation.

    Uses the OpenAI API to generate text completions with GPT models.
    Maintains backward compatibility with existing OpenAI client usage.
    """

    def __init__(self, api_key: str, model: str = "gpt-5.4-mini"):
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key
            model: Model name (default: gpt-5.4-mini)
        """
        super().__init__(api_key, model)
        self.client = OpenAI(api_key=api_key)

    def _generate_impl(self, request: TextGenerationRequest) -> TextGenerationResponse:
        """Generate text using OpenAI API.

        Args:
            request: Text generation request with messages and parameters

        Returns:
            TextGenerationResponse with generated text

        Raises:
            Exception: OpenAI API errors
        """
        # Use request model or default to instance model
        model = request.model or self.model

        # Convert Message dataclasses to OpenAI format
        messages = [
            {"role": msg.role, "content": msg.content} for msg in request.messages
        ]

        # Prepare API parameters
        api_params = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
            "max_completion_tokens": request.max_tokens,
        }

        # Add any extra provider-specific parameters
        if request.extra_params:
            api_params.update(request.extra_params)

        try:
            # Call OpenAI API
            response = self.client.chat.completions.create(**api_params)

            # Extract generated text
            text = response.choices[0].message.content.strip()

            # Build usage information
            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            logger.debug(f"OpenAI generation successful with model {model}")

            return TextGenerationResponse(
                text=text,
                provider="openai",
                model=model,
                usage=usage,
                raw_response=response,
            )

        except Exception as e:
            logger.error(f"OpenAI generation failed: {e}")
            raise
