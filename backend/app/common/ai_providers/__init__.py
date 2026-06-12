"""AI text generation provider abstraction layer.

This package provides a flexible abstraction for working with multiple
AI text generation providers (OpenAI, NVIDIA, Anthropic, etc.).

Usage:
    from app.common.ai_providers import ProviderFactory
    from app.common.ai_providers.models import Message, TextGenerationRequest

    provider = ProviderFactory.create()
    request = TextGenerationRequest(
        messages=[
            Message(role="system", content="You are a helpful assistant."),
            Message(role="user", content="Hello!"),
        ]
    )
    response = provider.generate(request)
    print(response.text)
"""

from .base import BaseTextProvider
from .factory import ProviderFactory
from .models import Message, TextGenerationRequest, TextGenerationResponse
from .protocol import TextGenerationProvider

__all__ = [
    "BaseTextProvider",
    "Message",
    "ProviderFactory",
    "TextGenerationProvider",
    "TextGenerationRequest",
    "TextGenerationResponse",
]
