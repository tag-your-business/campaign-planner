"""Orchestrates CaptionGenerator and PromptGenerator to produce content."""

from app.features.generation.caption import CaptionGenerator
from app.features.generation.prompt import PromptGenerator


class ContentService:
    def __init__(self):
        self.caption_gen = CaptionGenerator()
        self.prompt_gen = PromptGenerator()

    def generate(self, campaign_spec: dict) -> dict:
        caption = self.caption_gen.generate(campaign_spec)
        image_prompt = self.prompt_gen.generate(campaign_spec)
        return {"caption": caption, "image_prompt": image_prompt}
