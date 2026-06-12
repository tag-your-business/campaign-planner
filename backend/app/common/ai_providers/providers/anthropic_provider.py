"""Anthropic text generation provider implementation."""

import logging

from anthropic import Anthropic

from ..base import BaseTextProvider
from ..models import TextGenerationRequest, TextGenerationResponse

logger = logging.getLogger(__name__)


class AnthropicProvider(BaseTextProvider):
    """Anthropic Claude provider for text generation.

    Uses the Anthropic API to generate text completions with Claude models.
    Handles Anthropic's requirement for separate system prompts.
    """

    def __init__(self, api_key: str, model: str = "claude-opus-4-8"):
        """Initialize Anthropic provider.

        Args:
            api_key: Anthropic API key
            model: Model name (default: claude-opus-4-8)
        """
        super().__init__(api_key, model)
        self.client = Anthropic(api_key=api_key)

    def _generate_impl(self, request: TextGenerationRequest) -> TextGenerationResponse:
        """Generate text using Anthropic API.

        Args:
            request: Text generation request with messages and parameters

        Returns:
            TextGenerationResponse with generated text

        Raises:
            Exception: Anthropic API errors
        """
        # Use request model or default to instance model
        model = request.model or self.model

        # Anthropic requires system prompt separate from messages
        # Extract system message if present
        system_prompt = None
        user_messages = []

        for msg in request.messages:
            if msg.role == "system":
                # Anthropic expects single system prompt
                system_prompt = msg.content
            else:
                user_messages.append({"role": msg.role, "content": msg.content})

        # Prepare API parameters
        api_params = {
            "model": model,
            "max_tokens": request.max_tokens,
            "messages": user_messages,
        }

        # Add system prompt if present
        if system_prompt:
            api_params["system"] = system_prompt

        # Add temperature if not default
        if request.temperature != 0.7:
            api_params["temperature"] = request.temperature

        # Add any extra provider-specific parameters
        if request.extra_params:
            api_params.update(request.extra_params)

        try:
            # Call Anthropic API
            response = self.client.messages.create(**api_params)

            # Extract generated text
            # Anthropic returns content as a list of blocks
            text = response.content[0].text.strip()

            # Build usage information
            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": (
                        response.usage.input_tokens + response.usage.output_tokens
                    ),
                }

            logger.debug(f"Anthropic generation successful with model {model}")

            return TextGenerationResponse(
                text=text,
                provider="anthropic",
                model=model,
                usage=usage,
                raw_response=response,
            )

        except Exception as e:
            logger.error(f"Anthropic generation failed: {e}")
            raise
