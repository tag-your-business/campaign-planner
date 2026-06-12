"""Data models for AI text generation providers."""

from dataclasses import dataclass
from typing import Any


@dataclass
class Message:
    """Represents a chat message with role and content.

    Args:
        role: The role of the message sender (e.g., 'system', 'user',
            'assistant')
        content: The text content of the message
    """

    role: str
    content: str


@dataclass
class TextGenerationRequest:
    """Request model for text generation across providers.

    Args:
        messages: List of conversation messages
        model: Optional model name override (uses provider default if None)
        temperature: Sampling temperature (0.0 to 1.0)
        max_tokens: Maximum tokens to generate
        extra_params: Additional provider-specific parameters
    """

    messages: list[Message]
    model: str | None = None
    temperature: float = 0.7
    max_tokens: int = 1000
    extra_params: dict[str, Any] | None = None


@dataclass
class TextGenerationResponse:
    """Response model for text generation.

    Args:
        text: The generated text content
        provider: Name of the provider that generated the response
        model: Model name used for generation
        usage: Token usage information (if available)
        raw_response: Original provider response for debugging
    """

    text: str
    provider: str
    model: str
    usage: dict[str, Any] | None = None
    raw_response: Any | None = None
