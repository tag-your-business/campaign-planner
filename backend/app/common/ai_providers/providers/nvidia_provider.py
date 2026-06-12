"""NVIDIA text generation provider implementation."""

import logging

from openai import OpenAI

from ..base import BaseTextProvider
from ..models import TextGenerationRequest, TextGenerationResponse

logger = logging.getLogger(__name__)

NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"


class NvidiaProvider(BaseTextProvider):
    """NVIDIA API provider for text generation.

    Uses NVIDIA's OpenAI-compatible API with models like Llama.
    The OpenAI SDK is reused with a custom base_url pointing to NVIDIA's endpoint.
    """

    def __init__(self, api_key: str, model: str = "meta/llama-3.1-8b-instruct"):
        """Initialize NVIDIA provider.

        Args:
            api_key: NVIDIA API key (nvapi-...)
            model: Model name (default: meta/llama-3.1-8b-instruct)
        """
        super().__init__(api_key, model)
        self.client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=api_key)

    def _generate_impl(self, request: TextGenerationRequest) -> TextGenerationResponse:
        """Generate text using NVIDIA's OpenAI-compatible API.

        Args:
            request: Text generation request with messages and parameters

        Returns:
            TextGenerationResponse with generated text

        Raises:
            Exception: NVIDIA API errors
            ValueError: If the response contains no text content
        """
        model = request.model or self.model

        messages = [
            {"role": msg.role, "content": msg.content} for msg in request.messages
        ]

        api_params = {
            "model": model,
            "messages": messages,
            "temperature": request.temperature,
            "top_p": 0.7,
            "max_tokens": request.max_tokens,
            "stream": False,
        }

        if request.extra_params:
            api_params.update(request.extra_params)

        try:
            response = self.client.chat.completions.create(**api_params)

            content = response.choices[0].message.content
            if content is None:
                raise ValueError("NVIDIA API returned no text content")

            usage = None
            if response.usage:
                usage = {
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                }

            logger.debug(f"NVIDIA generation successful with model {model}")

            return TextGenerationResponse(
                text=content.strip(),
                provider="nvidia",
                model=model,
                usage=usage,
                raw_response=response,
            )

        except Exception as e:
            logger.error(f"NVIDIA generation failed: {e}")
            raise
