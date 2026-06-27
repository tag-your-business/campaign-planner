"""Mock OpenAI client for testing caption and image generation."""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MockChatMessage:
    """Mock OpenAI chat message."""

    def __init__(self, content: str):
        self.content = content


class MockChatChoice:
    """Mock OpenAI chat choice."""

    def __init__(self, message: MockChatMessage):
        self.message = message


class MockChatResponse:
    """Mock OpenAI chat completion response."""

    def __init__(self, content: str):
        self.choices = [MockChatChoice(MockChatMessage(content))]
        self.usage = None


class MockImageData:
    """Mock OpenAI image data."""

    def __init__(self, b64_json: str):
        self.b64_json = b64_json


class MockImageResponse:
    """Mock OpenAI image generation response."""

    def __init__(self, b64_json: str):
        self.data = [MockImageData(b64_json)]


class MockChatCompletions:
    """Mock OpenAI chat completions API."""

    def __init__(self, client: "MockOpenAIClient"):
        self.client = client

    def create(
        self, model: str, messages: List[Dict[str, str]], **kwargs: Any
    ) -> MockChatResponse:
        """Mock chat completion creation."""
        # Track invocation
        self.client.chat_invocations.append(
            {"model": model, "messages": messages, **kwargs}
        )

        # Simulate failure if configured
        if self.client.should_fail_chat:
            logger.error(f"Mock: Chat completion failed for model {model}")
            raise Exception("Mock OpenAI chat API error")

        # Return custom or default caption
        caption = (
            self.client.custom_caption or "Mock generated caption for your campaign"
        )
        logger.info(f"Mock: Generated chat completion with model {model}")
        return MockChatResponse(caption)


class MockImageGeneration:
    """Mock OpenAI image generation API."""

    def __init__(self, client: "MockOpenAIClient"):
        self.client = client

    def generate(
        self,
        model: str,
        prompt: str,
        n: int = 1,
        size: str = "1024x1024",
        **kwargs: Any,
    ) -> MockImageResponse:
        """Mock image generation."""
        # Track invocation
        self.client.image_invocations.append(
            {"model": model, "prompt": prompt, "n": n, "size": size, **kwargs}
        )

        # Simulate failure if configured
        if self.client.should_fail_image:
            logger.error(f"Mock: Image generation failed for model {model}")
            raise Exception("Mock OpenAI image API error")

        # Return custom or default base64 image
        image_b64 = (
            self.client.custom_image_b64 or "aW1hZ2VieXRlcw=="
        )  # b64("imagebytes")
        logger.info(f"Mock: Generated image with model {model}")
        return MockImageResponse(image_b64)


class MockResponsesResponse:
    """Mock OpenAI Responses API response (GPT-5+ models)."""

    def __init__(self, content: str):
        self.output_text = content
        self.usage = type("Usage", (), {"input_tokens": 10, "output_tokens": 5})()


class MockResponses:
    """Mock OpenAI Responses API (used by GPT-5+, o3, o4 models)."""

    def __init__(self, client: "MockOpenAIClient"):
        self.client = client

    def create(self, model: str, input: str, **kwargs: Any) -> MockResponsesResponse:
        """Mock responses.create call."""
        self.client.responses_invocations.append(
            {"model": model, "input": input, **kwargs}
        )

        if self.client.should_fail_chat:
            logger.error(f"Mock: Responses API failed for model {model}")
            raise Exception("Mock OpenAI chat API error")

        caption = (
            self.client.custom_caption or "Mock generated caption for your campaign"
        )
        logger.info(f"Mock: Generated response with model {model}")
        return MockResponsesResponse(caption)


class MockOpenAIClient:
    """
    Mock OpenAI client matching the SDK structure.

    Supports both:
    - Responses API (GPT-5+): client.responses.create() → response.output_text
    - Chat Completions API (GPT-4): client.chat.completions.create()
      → response.choices[0].message.content
    - Image generation: client.images.generate() → response.data[0].b64_json

    Usage:
        mock_client = MockOpenAIClient()
        # Responses API (gpt-5.4-mini)
        response = mock_client.responses.create(model="gpt-5.4-mini", input="Hello")
        caption = response.output_text

        # Chat Completions API (gpt-4o)
        response = mock_client.chat.completions.create(model="gpt-4o", messages=[...])
        caption = response.choices[0].message.content

        # Image generation (gpt-image-2)
        response = mock_client.images.generate(model="gpt-image-2", prompt="...")
        b64 = response.data[0].b64_json
    """

    def __init__(
        self,
        should_fail_chat: bool = False,
        should_fail_image: bool = False,
        custom_caption: Optional[str] = None,
        custom_image_b64: Optional[str] = None,
        custom_image_url: Optional[str] = None,
    ):
        """
        Initialize mock OpenAI client.

        Args:
            should_fail_chat: If True, both chat completions and responses.create raise
            should_fail_image: If True, image generation raises exceptions
            custom_caption: Custom caption to return (default: generic mock caption)
            custom_image_b64: Custom base64 image to return (default: mock value)
            custom_image_url: Ignored (kept for backward compatibility)
        """
        self.should_fail_chat = should_fail_chat
        self.should_fail_image = should_fail_image
        self.custom_caption = custom_caption
        self.custom_image_b64 = custom_image_b64

        # Initialize nested API interfaces
        self.chat = type("Chat", (), {"completions": MockChatCompletions(self)})()
        self.images = MockImageGeneration(self)
        self.responses = MockResponses(self)

        # Invocation tracking
        self.chat_invocations: List[Dict[str, Any]] = []
        self.image_invocations: List[Dict[str, Any]] = []
        self.responses_invocations: List[Dict[str, Any]] = []
