"""Mock AI provider for testing."""

from app.common.ai_providers import TextGenerationRequest, TextGenerationResponse


class MockProvider:
    """Mock text generation provider for testing.

    Returns predictable responses without making API calls.
    Useful for testing services that depend on AI providers.
    """

    def __init__(
        self,
        api_key: str = "mock-key",
        model: str = "mock-model",
        response_text: str = "Mock generated text",
    ):
        """Initialize mock provider.

        Args:
            api_key: Mock API key (ignored)
            model: Mock model name
            response_text: Text to return in responses
        """
        self.api_key = api_key
        self.model = model
        self.response_text = response_text
        self.call_count = 0
        self.last_request = None

    def generate(self, request: TextGenerationRequest) -> TextGenerationResponse:
        """Generate mock response.

        Args:
            request: The text generation request

        Returns:
            Mock TextGenerationResponse
        """
        self.call_count += 1
        self.last_request = request

        return TextGenerationResponse(
            text=self.response_text,
            provider="mock",
            model=request.model or self.model,
            usage={
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            },
            raw_response={"mock": True},
        )
