"""Generate gpt-image-1 image prompts using AI providers."""

import logging

from app.common.ai_providers import Message, ProviderFactory, TextGenerationRequest

logger = logging.getLogger(__name__)


class PromptGenerator:
    """Uses AI providers to generate rich, campaign-aware DALL-E image prompts.

    Supports multiple AI providers (OpenAI, NVIDIA, Anthropic) through
    abstraction layer. Provider selection is configured via environment
    variables.
    """

    SYSTEM_PROMPT = """\
You are an expert visual designer creating DALL-E image prompts for festival social media posts.

Your prompts must:
- Be descriptive and specific (800-1200 characters)
- Specify visual style, composition, lighting, colors, and mood
- Be tailored to the industry, audience, and brand tone
- Reference artistic style (e.g., photorealistic, illustrated, minimal, bold)
- Include a short header text rendered in the image (e.g., "Happy Diwali", "Happy Labour Day")
- Include a 1-2 sentence thematic body message appropriate to the festival and industry
- Use the brand colors prominently in the visual composition
- Be optimized for a square 1024x1024 social media post

Do NOT include in the image:
- Company name as the main headline or dominant title
- Company address, phone number, website, or any specific business details
- Company logo (it is added separately in post-processing)
- Any text that could be mistaken for factual company information

A soft, generic sentiment woven into the body text is acceptable
(e.g., "Wishing you joy this season", "We celebrate alongside you").
Keep company references warm but non-specific.

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
            campaign_spec: Contains event_name, industry, tone_keywords,
                brand_colors, locations, visual_style, primary_audience, etc.

        Returns:
            A detailed prompt string ready for gpt-image-1, including header and
            body text directives for the image.

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
                max_tokens=600,
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
        primary_audience = campaign_spec.get("primary_audience", "")
        visual_style = campaign_spec.get("visual_style", "")
        language = campaign_spec.get("language", "English")
        tone_keywords = campaign_spec.get("tone_keywords", [])

        # Handle brand_colors as dict {"primary": ..., "accent": ...} or legacy list
        brand_colors = campaign_spec.get("brand_colors", {})
        if isinstance(brand_colors, dict):
            primary = brand_colors.get("primary", "")
            accent = brand_colors.get("accent", "")
            colors_text = (
                f"primary {primary}, accent {accent}" if primary else "vibrant colors"
            )
        else:
            colors_text = (
                ", ".join(brand_colors)
                if brand_colors
                else "vibrant professional colors"
            )

        # Derive location string from the primary location entry
        locations = campaign_spec.get("locations", [])
        primary_loc = next((loc for loc in locations if loc.get("is_primary")), None)
        location_text = ""
        if primary_loc:
            parts = [
                p
                for p in [
                    primary_loc.get("city", ""),
                    primary_loc.get("state", ""),
                    primary_loc.get("country", ""),
                ]
                if p
            ]
            location_text = ", ".join(parts)

        tone_text = ", ".join(tone_keywords) if tone_keywords else "professional"

        lines = [
            f"Create a gpt-image-1 image generation prompt for a {industry} business's"
            f" {event_name} social media post.",
            "",
            f"Brand tone: {tone_text}",
            f"Brand colors: {colors_text}",
        ]

        if visual_style:
            lines.append(f"Visual style: {visual_style}")
        if primary_audience:
            lines.append(f"Target audience: {primary_audience}")
        if location_text:
            lines.append(f"Location context: {location_text}")

        lines.extend(
            [
                f"Image text language: {language}",
                "",
                "The image must include two text elements rendered visually:",
                f"1. A header greeting for {event_name} — short and celebratory"
                f" (e.g. 'Happy {event_name}' or a creative variant).",
                f"2. A 1-2 sentence thematic body message celebrating {event_name},"
                f" resonant with {primary_audience or 'the audience'} in {industry}.",
                "",
                f"Ground the visual scene in {location_text or 'the local culture'}"
                f" and make it relevant to {industry}."
                " No company name as headline, no address, no phone,"
                " no logo — those are added later.",
            ]
        )

        return "\n".join(lines)
