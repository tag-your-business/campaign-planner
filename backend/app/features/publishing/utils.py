"""Utility functions for publishing features."""

import httpx
from app.core.config import settings


async def get_facebook_photo_url(post_id: str, access_token: str | None = None) -> str:
    """
    Fetch the publicly accessible image URL from a Facebook photo post.

    This function makes a Graph API call to retrieve the image URL
    from a Facebook photo post. The URL can be used for Instagram
    publishing, which requires publicly accessible image URLs.

    Args:
        post_id: Facebook photo post ID
        access_token: Facebook access token (uses settings if not provided)

    Returns:
        Publicly accessible image URL (largest available size)

    Raises:
        ValueError: If the image URL cannot be retrieved
    """
    token = access_token or settings.facebook_access_token
    api_version = settings.facebook_api_version

    url = f"https://graph.facebook.com/{api_version}/{post_id}"
    params = {"fields": "images", "access_token": token}

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.get(url, params=params)

        if response.status_code == 200:
            result = response.json()
            images = result.get("images", [])

            if not images:
                raise ValueError(f"No images found for post {post_id}")

            # Return the largest image (first in the list)
            image_url = images[0].get("source")
            if not image_url:
                raise ValueError(f"No image URL found for post {post_id}")

            return image_url
        else:
            error_msg = response.text
            raise ValueError(
                f"Failed to fetch photo URL: {response.status_code} - {error_msg}"
            )
