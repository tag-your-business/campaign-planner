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


class MockImageData:
    """Mock OpenAI image data."""

    def __init__(self, url: str):
        self.url = url


class MockImageResponse:
    """Mock OpenAI image generation response."""

    def __init__(self, url: str):
        self.data = [MockImageData(url)]


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

        # Return custom or default image URL
        image_url = (
            self.client.custom_image_url
            or "https://mock-openai.com/generated-image.png"
        )
        logger.info(f"Mock: Generated image with model {model}")
        return MockImageResponse(image_url)


class MockOpenAIClient:
    """
    Mock OpenAI client matching the SDK structure.

    Usage:
        mock_client = MockOpenAIClient()
        response = mock_client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Hello"}]
        )
        caption = response.choices[0].message.content

        response = mock_client.images.generate(
            model="dall-e-3",
            prompt="A beautiful sunset",
            n=1,
            size="1024x1024"
        )
        url = response.data[0].url
    """

    def __init__(
        self,
        should_fail_chat: bool = False,
        should_fail_image: bool = False,
        custom_caption: Optional[str] = None,
        custom_image_url: Optional[str] = None,
    ):
        """
        Initialize mock OpenAI client.

        Args:
            should_fail_chat: If True, chat completions will raise exceptions
            should_fail_image: If True, image generation will raise exceptions
            custom_caption: Custom caption to return (default: generic mock caption)
            custom_image_url: Custom image URL to return (default: mock URL)
        """
        self.should_fail_chat = should_fail_chat
        self.should_fail_image = should_fail_image
        self.custom_caption = custom_caption
        self.custom_image_url = custom_image_url

        # Initialize nested API interfaces
        self.chat = type("Chat", (), {"completions": MockChatCompletions(self)})()
        self.images = MockImageGeneration(self)

        # Invocation tracking
        self.chat_invocations: List[Dict[str, Any]] = []
        self.image_invocations: List[Dict[str, Any]] = []
