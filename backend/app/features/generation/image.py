"""Generates images via OpenAI DALL-E and saves to campaigns dir."""

import logging
from pathlib import Path

import httpx
from app.core.config import settings
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


class ImageService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def generate(self, prompt: str, output_path: Path) -> Path:
        """Generate an image with DALL-E and write it to output_path.

        Args:
            prompt: DALL-E image prompt.
            output_path: Destination file path for the generated PNG.

        Returns:
            The output_path after the file is written.

        Raises:
            Exception: If all retry attempts fail.
        """
        try:
            response = self.client.images.generate(
                model=settings.openai_image_model,
                prompt=prompt,
                n=1,
                size="1024x1024",
            )
            image_url = response.data[0].url
            image_bytes = httpx.get(image_url).content

            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_bytes(image_bytes)

            logger.info(f"Saved generated image to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to generate image: {e}")
            raise
