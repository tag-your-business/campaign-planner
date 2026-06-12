"""Generate DALL-E image prompts using AI providers."""

import logging

from app.common.ai_providers import Message, ProviderFactory, TextGenerationRequest

logger = logging.getLogger(__name__)


class PromptGenerator:
    """Uses AI providers to generate rich, campaign-aware DALL-E image prompts.

    Supports multiple AI providers (OpenAI, NVIDIA, Anthropic) through
    abstraction layer. Provider selection is configured via environment
    variables.
    """

    SYSTEM_PROMPT = """You are an expert visual artist and marketing specialist who creates
detailed image generation prompts for DALL-E.

Your prompts should:
- Be descriptive and specific (200-350 characters)
- Specify visual style, composition, lighting, colors, and mood
- Be tailored to the specific industry and brand tone
- Reference artistic style (e.g., photorealistic, illustrated, minimal, bold)
- Never include text, words, or lettering in the image
- Be optimized for a square 1024x1024 social media post

Output ONLY the prompt text with no preamble, labels, or commentary."""

    def __init__(self, provider_name: str | None = None):
        """Initialize the prompt generator with configured AI provider.

        Args:
            provider_name: Optional provider override ('openai', 'nvidia',
                'anthropic'). If None, uses TEXT_GENERATION_PROVIDER from
                settings. Useful for testing or special cases.
        """
        self.provider = ProviderFactory.create(provider_name)

    def generate(self, campaign_spec: dict) -> str:
        """Generate a DALL-E prompt for the given campaign spec via AI provider.

        Uses the abstraction layer to support multiple providers. Retry
        logic is handled automatically by the provider.

        Args:
            campaign_spec: Contains event_name, industry, tone, brand_colors, etc.

        Returns:
            A detailed prompt string ready for DALL-E.

        Raises:
            Exception: If all retry attempts fail.
        """
        try:
            user_prompt = self._build_user_prompt(campaign_spec)

            request = TextGenerationRequest(
                messages=[
                    Message(role="system", content=self.SYSTEM_PROMPT),
                    Message(role="user", content=user_prompt),
                ],
                model=None,  # Use provider's default model
                temperature=0.7,
                max_tokens=500,
            )

            response = self.provider.generate(request)
            prompt = response.text.strip()

            logger.info(
                f"Generated image prompt for {campaign_spec.get('company_name')} - "
                f"{campaign_spec.get('event_name')} "
                f"using {response.provider} ({response.model})"
            )
            return prompt

        except Exception as e:
            logger.error(
                f"Failed to generate image prompt for "
                f"{campaign_spec.get('company_name')}: {e}"
            )
            raise

    def _build_user_prompt(self, campaign_spec: dict) -> str:
        """Build the user prompt with campaign context."""
        event_name = campaign_spec.get("event_name", "Special Event")
        industry = campaign_spec.get("industry", "business")
        tone = campaign_spec.get("tone", "professional")
        brand_colors = campaign_spec.get("brand_colors", [])
        colors_text = (
            ", ".join(brand_colors) if brand_colors else "vibrant professional colors"
        )

        return (
            f"Create a DALL-E image generation prompt for a {industry} business's "
            f"{event_name} social media post.\n\n"
            f"Brand tone: {tone}\n"
            f"Brand colors: {colors_text}\n\n"
            f"The image should immediately convey the {event_name} celebration "
            f"while feeling relevant and authentic to the {industry} industry."
        )
