"""
NVIDIA API Client
A static class for interacting with NVIDIA's chat completion API.
"""

import base64
from typing import Optional

import requests


class NvidiaAPIClient:
    """Static class for NVIDIA API interactions."""

    INVOKE_URL = "https://integrate.api.nvidia.com/v1/chat/completions"
    # TODO: Move API key to environment variable for security
    API_KEY = "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"

    @staticmethod
    def read_b64(path: str) -> str:
        """
        Read a file and return its base64 encoded content.

        Args:
            path: Path to the file to encode

        Returns:
            Base64 encoded string of file contents
        """
        with open(path, "rb") as f:
            return base64.b64encode(f.read()).decode()

    @staticmethod
    def make_request(
        message: str,
        system_prompt: Optional[str] = None,
        model: str = "meta/llama-3.1-8b-instruct",
        stream: bool = False,
        max_tokens: int = 16384,
        temperature: float = 1.00,
        top_p: float = 0.95,
    ) -> None:
        """
        Make a request to NVIDIA's chat completion API.

        Args:
            message: The user message to send
            system_prompt: Optional system prompt to set context
            model: The model to use for completion
            stream: Whether to stream the response
            max_tokens: Maximum tokens in response
            temperature: Sampling temperature
            top_p: Top-p sampling parameter
        """
        headers = {
            "Authorization": "Bearer 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",
            "Accept": "text/event-stream" if stream else "application/json",
        }

        # Build messages array with optional system prompt
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": message})

        payload = {
            "model": model,
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stream": stream,
            "chat_template_kwargs": {"enable_thinking": True},
        }

        response = requests.post(
            NvidiaAPIClient.INVOKE_URL,
            headers=headers,
            json=payload,
            stream=stream,
            timeout=30,
        )

        if stream:
            for line in response.iter_lines():
                if line:
                    print(line.decode("utf-8"))
        else:
            print(response.json())

    @staticmethod
    def main() -> None:
        """Main entry point for the client."""
        # System prompt for social media content creation
        system_prompt = (
            "You are a professional social media content creator "
            "specializing in creating engaging, brand-appropriate captions "
            "for business social media posts.\n\n"
            "Your captions should:\n"
            "- Be 150-300 characters long\n"
            "- Match the specified brand tone and industry\n"
            "- Include 3-5 relevant hashtags\n"
            "- Be engaging and encourage interaction\n"
            "- Celebrate the specific event/holiday mentioned\n"
            "- Be professional and on-brand\n\n"
            "Format: Write the caption text followed by hashtags on the same or next line."
        )

        # Sample campaign spec
        campaign_spec = {
            "event_name": "New Year's Day",
            "company_name": "TechFlow Solutions",
            "industry": "Software Development",
            "tone": "Professional yet friendly",
            "event_tags": ["newyear", "2026", "innovation", "technology", "freshstart"],
        }

        # Build user prompt with campaign spec
        user_message = f"""Create a social media caption for the following campaign:

Event: {campaign_spec['event_name']}
Company: {campaign_spec['company_name']}
Industry: {campaign_spec['industry']}
Tone: {campaign_spec['tone']}
Event Tags: {', '.join(campaign_spec['event_tags'])}

Please create an engaging caption that follows the guidelines."""

        print(f"Campaign Spec: {campaign_spec}\n")
        print("Generating caption...\n")

        NvidiaAPIClient.make_request(
            message=user_message, system_prompt=system_prompt, stream=False
        )


if __name__ == "__main__":
    NvidiaAPIClient.main()
