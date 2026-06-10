"""Generate prompts for AI image generation based on campaign specifications."""


class PromptGenerator:
    """Generates DALL-E prompts for campaign images based on company and event context."""

    # Industry-specific keywords to enhance relevance
    INDUSTRY_KEYWORDS = {
        "dental": "teeth, smiles, oral health, dental care, bright smile, healthy teeth",
        "healthcare": "wellness, health, care, medical, patient care, healthy living",
        "restaurant": "food, dining, delicious, culinary, cuisine, tasty",
        "retail": "shopping, products, deals, store, merchandise, quality",
        "fitness": "exercise, workout, health, strength, active lifestyle, wellness",
        "beauty": "beauty, skincare, cosmetics, makeup, radiance, self-care",
        "default": "professional, quality, service, excellence, customer satisfaction",
    }

    IMAGE_PROMPT_TEMPLATE = """Create a professional, vibrant social media image for {event_name}.

Industry: {industry}
Brand style: {tone}, modern, eye-catching, engaging
Visual elements: {industry_keywords}
Color palette: {brand_colors}
Composition: Clean, uncluttered design suitable for social media posts
Style: Professional marketing material with celebratory {event_name} theme

The image should be visually appealing, on-brand, and immediately convey the {event_name} \
celebration while relating to the {industry} industry."""

    def generate(self, campaign_spec: dict) -> str:
        """
        Generate a DALL-E image prompt from campaign specifications.

        Args:
            campaign_spec: Dictionary containing:
                - event_name: Name of the event/holiday
                - industry: Company industry (dental, healthcare, etc.)
                - tone: Brand tone (professional, friendly, etc.)
                - brand_colors: List of hex color codes

        Returns:
            Formatted prompt string for DALL-E image generation
        """
        industry = campaign_spec.get("industry", "general")
        industry_keywords = self.INDUSTRY_KEYWORDS.get(
            industry, self.INDUSTRY_KEYWORDS["default"]
        )

        # Format brand colors for natural language
        brand_colors = campaign_spec.get("brand_colors", [])
        colors_text = (
            ", ".join(brand_colors) if brand_colors else "vibrant, professional colors"
        )

        prompt = self.IMAGE_PROMPT_TEMPLATE.format(
            event_name=campaign_spec.get("event_name", "Special Event"),
            industry=industry,
            tone=campaign_spec.get("tone", "professional"),
            industry_keywords=industry_keywords,
            brand_colors=colors_text,
        )

        return prompt.strip()
