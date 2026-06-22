"""OpenAI text generation provider implementation."""

import logging

from openai import OpenAI

from ..base import BaseTextProvider
from ..models import TextGenerationRequest, TextGenerationResponse

logger = logging.getLogger(__name__)

# Models that use the new Responses API (GPT-5 family and newer)
RESPONSES_API_MODELS = ("gpt-5", "o3", "o4")


class OpenAIProvider(BaseTextProvider):
    """OpenAI GPT provider for text generation.

    Uses the OpenAI API to generate text completions with GPT models.
    Supports both legacy Chat Completions API (GPT-4) and new Responses API (GPT-5+).
    """

    def __init__(self, api_key: str, model: str = "gpt-5.4-mini"):
        super().__init__(api_key, model)
        self.client = OpenAI(api_key=api_key)

    def _uses_responses_api(self, model: str) -> bool:
        """Check if the model uses the new Responses API."""
        return any(model.startswith(prefix) for prefix in RESPONSES_API_MODELS)

    def _generate_impl(self, request: TextGenerationRequest) -> TextGenerationResponse:
        """Generate text using OpenAI API.

        Uses Responses API for GPT-5+ models, Chat Completions API for GPT-4 models.
        """
        model = request.model or self.model

        if self._uses_responses_api(model):
            return self._generate_with_responses_api(request, model)
        else:
            return self._generate_with_chat_completions(request, model)

    def _generate_with_responses_api(
        self, request: TextGenerationRequest, model: str
    ) -> TextGenerationResponse:
        """Generate text using the new Responses API (GPT-5+ models)."""
        # Build input from messages - combine system and user prompts
        input_parts = []
        instructions = None

        for msg in request.messages:
            if msg.role == "system":
                instructions = msg.content
            else:
                input_parts.append(msg.content)

        input_text = "\n\n".join(input_parts)

        # Prepare API parameters for Responses API
        api_params = {
            "model": model,
            "input": input_text,
            "max_output_tokens": request.max_tokens,
        }

        # Add system instructions if present
        if instructions:
            api_params["instructions"] = instructions

        # Add extra params (e.g., reasoning.effort, text.verbosity)
        if request.extra_params:
            api_params.update(request.extra_params)

        try:
            response = self.client.responses.create(**api_params)

            text = response.output_text.strip() if response.output_text else ""

            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.input_tokens,
                    "completion_tokens": response.usage.output_tokens,
                    "total_tokens": (
                        response.usage.input_tokens + response.usage.output_tokens
                    ),
                }

            logger.debug(f"OpenAI Responses API generation successful: {model}")

            return TextGenerationResponse(
                text=text,
                provider="openai",
                model=model,
                usage=usage,
                raw_response=response,
            )

        except Exception as e:
            logger.error(f"OpenAI Responses API generation failed: {e}")
            raise

    def _generate_with_chat_completions(
        self, request: TextGenerationRequest, model: str
    ) -> TextGenerationResponse:
        """Generate text using legacy Chat Completions API (GPT-4 models)."""
        messages = [
            {"role": msg.role, "content": msg.content} for msg in request.messages
        ]

        api_params = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
            "max_completion_tokens": request.max_tokens,
        }

        if request.extra_params:
            api_params.update(request.extra_params)

        try:
            response = self.client.chat.completions.create(**api_params)

            text = response.choices[0].message.content.strip()

            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            logger.debug(f"OpenAI Chat Completions generation successful: {model}")

            return TextGenerationResponse(
                text=text,
                provider="openai",
                model=model,
                usage=usage,
                raw_response=response,
            )

        except Exception as e:
            logger.error(f"OpenAI Chat Completions generation failed: {e}")
            raise
