"""NVIDIA text generation provider implementation."""

import logging

import requests

from ..base import BaseTextProvider
from ..models import TextGenerationRequest, TextGenerationResponse

logger = logging.getLogger(__name__)


class NvidiaProvider(BaseTextProvider):
    """NVIDIA API provider for text generation.

    Uses NVIDIA's chat completion API with models like Llama.
    Removes hardcoded API keys for better security.
    """

    INVOKE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"

    def __init__(self, api_key: str, model: str = "meta/llama-3.1-8b-instruct"):
        """Initialize NVIDIA provider.

        Args:
            api_key: NVIDIA API key (nvapi-...)
            model: Model name (default: meta/llama-3.1-8b-instruct)
        """
        super().__init__(api_key, model)

    def _generate_impl(self, request: TextGenerationRequest) -> TextGenerationResponse:
        """Generate text using NVIDIA API.

        Args:
            request: Text generation request with messages and parameters

        Returns:
            TextGenerationResponse with generated text

        Raises:
            requests.exceptions.RequestException: NVIDIA API errors
        """
        # Use request model or default to instance model
        model = request.model or self.model

        # Convert Message dataclasses to NVIDIA format
        messages = [
            {"role": msg.role, "content": msg.content} for msg in request.messages
        ]

        # Prepare API parameters
        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            "stream": False,
        }

        # Add NVIDIA-specific defaults and extra params
        payload.setdefault("top_p", 0.95)
        payload.setdefault("chat_template_kwargs", {"enable_thinking": True})

        # Merge any extra provider-specific parameters
        if request.extra_params:
            payload.update(request.extra_params)

        # Prepare headers
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json",
            "Content-Type": "application/json",
        }

        try:
            # Call NVIDIA API
            response = requests.post(
                self.INVOKE_URL,
                headers=headers,
                json=payload,
                timeout=30,
            )
            response.raise_for_status()

            # Parse response
            response_data = response.json()

            # Extract generated text (similar to OpenAI format)
            text = response_data["choices"][0]["message"]["content"].strip()

            # Build usage information if available
            usage = None
            if "usage" in response_data:
                usage = {
                    "prompt_tokens": response_data["usage"].get("prompt_tokens"),
                    "completion_tokens": response_data["usage"].get(
                        "completion_tokens"
                    ),
                    "total_tokens": response_data["usage"].get("total_tokens"),
                }

            logger.debug(f"NVIDIA generation successful with model {model}")

            return TextGenerationResponse(
                text=text,
                provider="nvidia",
                model=model,
                usage=usage,
                raw_response=response_data,
            )

        except requests.exceptions.RequestException as e:
            logger.error(f"NVIDIA API request failed: {e}")
            raise
        except (KeyError, IndexError) as e:
            logger.error(f"Failed to parse NVIDIA response: {e}")
            raise ValueError(f"Invalid NVIDIA API response format: {e}")
