"""Generate DALL-E image prompts using Claude."""

import logging

from anthropic import Anthropic
from app.core.config import settings
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class PromptGenerator:
    """Uses Claude to generate rich, campaign-aware DALL-E image prompts."""

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

    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key)
        self.model = settings.anthropic_text_model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def generate(self, campaign_spec: dict) -> str:
        """Generate a DALL-E prompt for the given campaign spec via Claude.

        Args:
            campaign_spec: Contains event_name, industry, tone, brand_colors, etc.

        Returns:
            A detailed prompt string ready for DALL-E.

        Raises:
            Exception: If all retry attempts fail.
        """
        try:
            user_prompt = self._build_user_prompt(campaign_spec)

            response = self.client.messages.create(
                model=self.model,
                max_tokens=500,
                system=self.SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_prompt}],
            )

            prompt = response.content[0].text.strip()
            logger.info(
                f"Generated image prompt for {campaign_spec.get('company_name')} - "
                f"{campaign_spec.get('event_name')}"
            )
            return prompt

        except Exception as e:
            logger.error(
                f"Failed to generate image prompt for {campaign_spec.get('company_name')}: {e}"
            )
            raise

    def _build_user_prompt(self, campaign_spec: dict) -> str:
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
