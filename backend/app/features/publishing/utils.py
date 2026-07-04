"""Utility functions for publishing features."""

import logging
from datetime import datetime, timezone

import httpx
from app.core.config import settings

logger = logging.getLogger(__name__)


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


async def check_facebook_token_health() -> None:
    """
    Validate the configured Facebook access token at startup.

    Logs the token status (valid / expiring / invalid) and never raises,
    so application startup is not blocked.
    """
    token = settings.facebook_access_token
    if not token:
        logger.warning("FACEBOOK_ACCESS_TOKEN not set; Facebook publishing disabled")
        return

    base_url = f"https://graph.facebook.com/{settings.facebook_api_version}"
    app_id = settings.facebook_app_id
    app_secret = settings.facebook_app_secret

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            if app_id and app_secret:
                response = await client.get(
                    f"{base_url}/debug_token",
                    params={
                        "input_token": token,
                        "access_token": f"{app_id}|{app_secret}",
                    },
                )
                if response.status_code != 200:
                    logger.warning(
                        f"Could not verify Facebook token (HTTP {response.status_code}) — "
                        "check FACEBOOK_APP_ID/FACEBOOK_APP_SECRET"
                    )
                    return
                data = response.json().get("data", {})
                if not data.get("is_valid"):
                    logger.error(
                        "Facebook token is INVALID — publishing will fail. "
                        "Re-run get_facebook_page_token.py"
                    )
                elif data.get("expires_at", 0) == 0:
                    logger.info("Facebook token valid (never expires)")
                else:
                    expires = datetime.fromtimestamp(
                        data["expires_at"], tz=timezone.utc
                    )
                    logger.warning(
                        f"Facebook token valid but expires {expires:%Y-%m-%d %H:%M UTC} — "
                        "use a never-expiring Page token (get_facebook_page_token.py)"
                    )
            else:
                response = await client.get(
                    f"{base_url}/me", params={"access_token": token}
                )
                if response.status_code == 200:
                    logger.info(
                        "Facebook token valid (expiry unknown; set FACEBOOK_APP_ID/"
                        "FACEBOOK_APP_SECRET for the full check)"
                    )
                elif response.json().get("error", {}).get("code") == 190:
                    logger.error(
                        "Facebook token is INVALID — publishing will fail. "
                        "Re-run get_facebook_page_token.py"
                    )
                else:
                    logger.warning(
                        f"Could not verify Facebook token (HTTP {response.status_code})"
                    )
    except Exception as e:
        logger.warning(f"Facebook token check skipped: {e}")
