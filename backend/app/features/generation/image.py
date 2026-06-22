"""Generates images via OpenAI gpt-image-2 and saves to campaigns dir."""

import base64
import logging
import shutil
from pathlib import Path

from app.core.config import settings
from openai import OpenAI
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

FALLBACK_IMAGE_PATH = Path(settings.data_dir) / "assets" / "fallback_image.png"


class ImageService:
    """Service for generating images via OpenAI image models."""

    def __init__(
        self,
        model: str | None = None,
        size: str | None = None,
        quality: str | None = None,
    ):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = model or settings.openai_image_model
        self.size = size or settings.openai_image_size
        self.quality = quality or settings.openai_image_quality

    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10),
        reraise=True,
    )
    def generate(self, prompt: str, output_path: Path) -> Path:
        """Generate an image and write it to output_path.

        When settings.use_fallback_image is True, skips the API call and
        copies the local placeholder instead — useful for testing branding
        without consuming API credits.

        Args:
            prompt: Image generation prompt.
            output_path: Destination file path for the generated PNG.

        Returns:
            The output_path after the file is written.

        Raises:
            Exception: If all retry attempts fail.
        """
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if settings.use_fallback_image:
            shutil.copy2(FALLBACK_IMAGE_PATH, output_path)
            logger.info(f"Using fallback image (skipping API call) -> {output_path}")
            return output_path

        try:
            logger.info(f"Generating image with model: {self.model}")
            response = self.client.images.generate(
                model=self.model,
                prompt=prompt,
                n=1,
                size=self.size,
                quality=self.quality,
            )
            image_bytes = base64.b64decode(response.data[0].b64_json)
            output_path.write_bytes(image_bytes)

            logger.info(f"Saved generated image to {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Failed to generate image: {e}")
            raise
