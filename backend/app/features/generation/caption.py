"""Generate social media captions using GPT-4o-mini."""

import logging

from app.core.config import settings
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class CaptionGenerator:
    """Generates engaging social media captions using GPT-4o-mini with retry logic."""

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

    def __init__(self):
        """Initialize the caption generator with OpenAI client."""
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_text_model

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def generate(self, campaign_spec: dict) -> str:
        """
        Generate a social media caption using GPT-4o-mini with retry logic.

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

            # Call GPT-4o-mini
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": self.CAPTION_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.7,  # Creative but consistent
                max_tokens=200,
            )

            caption = response.choices[0].message.content.strip()
            logger.info(
                f"Generated caption for {campaign_spec.get('company_name')} - "
                f"{campaign_spec.get('event_name')}"
            )

            return caption

        except Exception as e:
            logger.error(
                f"Failed to generate caption for {campaign_spec.get('company_name')}: {e}"
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
