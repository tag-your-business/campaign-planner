"""Generate social media captions using AI providers."""

import logging

from app.common.ai_providers import Message, ProviderFactory, TextGenerationRequest

logger = logging.getLogger(__name__)


class CaptionGenerator:
    """Generates social media captions using configurable AI providers.

    Supports multiple AI providers (OpenAI, NVIDIA, Anthropic) through
    abstraction layer. Provider selection is configured via environment
    variables.
    """

    CAPTION_SYSTEM_PROMPT = (
        """You are a professional social media content creator """
        """specializing in creating engaging, brand-appropriate captions """
        """for business social media posts.

Your captions should:
- Be 150-300 characters long
- Match the specified brand tone and industry
- Include 3-5 relevant hashtags
- Be engaging and encourage interaction
- Celebrate the specific event/holiday mentioned
- Be professional and on-brand

Format: Write the caption text followed by hashtags on the same or next line."""
    )

    def __init__(self, provider_name: str | None = None):
        """Initialize the caption generator with configured AI provider.

        Args:
            provider_name: Optional provider override ('openai', 'nvidia',
                'anthropic'). If None, uses TEXT_GENERATION_PROVIDER from
                settings. Useful for testing or special cases.
        """
        self.provider = ProviderFactory.create(provider_name)

    def generate(self, campaign_spec: dict) -> str:
        """Generate a social media caption using configured AI provider.

        Uses the abstraction layer to support multiple providers. Retry
        logic is handled automatically by the provider.

        Args:
            campaign_spec: Dictionary containing:
                - event_name: Name of the event/holiday
                - company_name: Company name
                - industry: Company industry
                - tone: Brand tone (professional, friendly, etc.)
                - event_tags: List of event tags

        Returns:
            Generated caption string with hashtags

        Raises:
            Exception: If all retry attempts fail
        """
        try:
            # Build context-rich user prompt
            user_prompt = self._build_user_prompt(campaign_spec)

            # Build request using abstraction layer
            request = TextGenerationRequest(
                messages=[
                    Message(role="system", content=self.CAPTION_SYSTEM_PROMPT),
                    Message(role="user", content=user_prompt),
                ],
                model=None,  # Use provider's default model
                temperature=0.7,  # Creative but consistent
                max_tokens=200,
            )

            # Generate caption using provider
            response = self.provider.generate(request)
            caption = response.text

            logger.info(
                f"Generated caption for {campaign_spec.get('company_name')} - "
                f"{campaign_spec.get('event_name')} "
                f"using {response.provider} ({response.model})"
            )

            return caption

        except Exception as e:
            logger.error(
                f"Failed to generate caption for "
                f"{campaign_spec.get('company_name')}: {e}"
            )
            raise

    def _build_user_prompt(self, campaign_spec: dict) -> str:
        """Build the user prompt with campaign context."""
        event_name = campaign_spec.get("event_name", "Special Event")
        company_name = campaign_spec.get("company_name", "our company")
        industry = campaign_spec.get("industry", "business")
        tone = campaign_spec.get("tone", "professional")
        event_tags = campaign_spec.get("event_tags", [])

        tags_context = f" (Event type: {', '.join(event_tags)})" if event_tags else ""

        prompt = f"""Create a social media caption for {company_name}, a {industry} business, \
celebrating {event_name}{tags_context}.

Brand tone: {tone}

The caption should be engaging, on-brand, and encourage audience interaction."""

        return prompt
