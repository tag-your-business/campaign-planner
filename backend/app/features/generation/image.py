"""Generates images via OpenAI DALL-E and saves to campaigns dir."""

from pathlib import Path

import httpx
from openai import OpenAI

from app.core.config import settings


class ImageService:
    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)

    def generate(self, prompt: str, output_path: Path) -> Path:
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
        return output_path
