"""Generate gpt-image-2 image prompts using AI providers."""

import logging
import textwrap

from app.common.ai_providers import Message, ProviderFactory, TextGenerationRequest

logger = logging.getLogger(__name__)


class PromptGenerator:
    """Uses AI providers to generate rich, campaign-aware DALL-E image prompts.

    Supports multiple AI providers (OpenAI, NVIDIA, Anthropic) through
    abstraction layer. Provider selection is configured via environment
    variables.
    """

    SYSTEM_PROMPT = textwrap.dedent("""\
        You are an expert art director writing image generation prompts for gpt-image-2.

        OUTPUT FORMAT — always use these five labeled sections, separated by blank lines:

        SCENE: Background environment, time of day, setting, atmosphere.
        SUBJECT: Main visual focus — what or who dominates the frame.
        DETAILS: Lighting source and quality, materials/textures, camera angle/framing, mood.
        TEXT: Header and body text content only.
        CONSTRAINTS: What must not appear or drift.

        RULES:
        - Use exactly one dominant visual style keyword per prompt \
        (e.g. "photorealistic" OR "flat illustration" — never both). \
        Place it in the DETAILS section.
        - Describe visuals concretely. Avoid vague praise words \
        (stunning, cinematic, masterpiece, ultra-detailed, 8K).
        - TEXT section: wrap every literal string in double quotes. Do NOT specify font, \
        color, or placement — let the image model decide all styling. The header and body \
        must be treated as a grouped unit. Spell unusual words letter-by-letter if needed.
        - TEXT section must include ONLY the header and body. No other text or decorative \
        type anywhere in the image.
        - Location/cultural context informs the visual scene only — never rendered as text \
        in the image.
        - If human subjects are present, they must face toward or at an angle toward \
        the viewer. Exception: gaze directed at a natural focal point \
        (fireworks, a dish, a celebration object) where looking away is contextually motivated.
        - DETAILS must reference both brand colors by hex value as tonal influences \
        on the overall palette — not as color assignments to specific surfaces or elements.
        - CONSTRAINTS must list: brand color hex codes as scene palette hints; no logos, \
        no watermarks, no company information; primary subjects within the central 85% \
        of the frame; no focal elements near the edges.

        Output ONLY the five-section prompt. No preamble, no labels outside the sections, \
        no commentary.""").strip()

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
            A structured five-section prompt ready for gpt-image-2, with header
            and body text elements locked in the TEXT section.

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
                max_tokens=800,
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
        visual_style = campaign_spec.get("visual_style") or "photorealistic"
        language = campaign_spec.get("language", "English")
        tone_keywords = campaign_spec.get("tone_keywords", [])

        # Handle brand_colors as dict {"primary": ..., "accent": ...} or legacy list
        brand_colors = campaign_spec.get("brand_colors", {})
        if isinstance(brand_colors, dict):
            primary = brand_colors.get("primary", "")
            accent = brand_colors.get("accent", "")
            values = ", ".join(filter(None, [primary, accent]))
            colors_text = (
                f"palette anchors (scene influence only, not fills): {values}"
                if values
                else "natural vibrant tones"
            )
        else:
            values = ", ".join(brand_colors) if brand_colors else ""
            colors_text = (
                f"palette anchors (scene influence only, not fills): {values}"
                if values
                else "natural vibrant tones"
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
        header_example = f"Happy {event_name}"

        lines = [
            f"Generate a {event_name} social media image prompt for a {industry} business.",
            "",
            f"Industry: {industry}",
            f"Brand tone: {tone_text}",
            f"Brand colors: {colors_text}",  # palette influence, not fill assignments
        ]

        lines.append(f"Visual style: {visual_style}")
        if primary_audience:
            lines.append(f"Target audience: {primary_audience}")
        if location_text:
            lines.append(
                f"Scene cultural context (visual reference only — not text): {location_text}"
            )

        body_audience = (
            f" and resonant with {primary_audience}" if primary_audience else ""
        )
        header_line = (
            f"  Header: a short {event_name} greeting"
            f' — e.g. "{header_example}" or a creative variant.'
        )
        body_line = (
            f"  Body: 1-2 sentences celebrating {event_name},"
            f" relevant to {industry}{body_audience}."
        )
        lines.extend(
            [
                f"Image text language: {language}",
                "",
                "TEXT elements to include:",
                header_line,
                body_line,
            ]
        )

        return "\n".join(lines)
