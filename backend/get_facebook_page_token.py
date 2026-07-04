#!/usr/bin/env python3
"""
Generate a never-expiring Facebook Page access token.

Exchanges a short-lived user token (from the Graph API Explorer) for a
long-lived user token, then fetches the Page access token. Page tokens
obtained this way have no expiration date — Meta only invalidates them on
password change, permission revocation, or ~90 days of user inactivity
on the app.

Steps:
    1. Reveal your App Secret: https://developers.facebook.com/apps
       -> your app -> App settings -> Basic -> App Secret -> Show.
    2. Get a short-lived user token from
       https://developers.facebook.com/tools/explorer/ (select your app,
       grant pages_manage_posts and pages_read_engagement).
    3. Run from the backend directory:
       poetry run python get_facebook_page_token.py <short-lived-token> \\
           --app-id <app-id> --app-secret <app-secret>

--app-id / --app-secret default to FACEBOOK_APP_ID / FACEBOOK_APP_SECRET
from .env when set there.
"""

import argparse
import hashlib
import hmac
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings  # noqa: E402

GRAPH_URL = f"https://graph.facebook.com/{settings.facebook_api_version}"

APP_SECRET_HELP = (
    "Reveal it at https://developers.facebook.com/apps -> your app "
    "-> App settings -> Basic -> App Secret -> Show"
)


def appsecret_proof(token: str, app_secret: str) -> str:
    return hmac.new(app_secret.encode(), token.encode(), hashlib.sha256).hexdigest()


def graph_get(url: str, params: dict[str, str]) -> dict:
    response = httpx.get(url, params=params, timeout=30.0)
    if response.status_code == 200:
        return response.json()

    try:
        error = response.json()["error"]
    except Exception:
        error = {"message": response.text}
    print(
        f"Graph API error {response.status_code}: {error.get('message')}",
        file=sys.stderr,
    )
    if error.get("code") == 190:
        print(
            "Token invalid or expired. Get a fresh short-lived token from "
            "https://developers.facebook.com/tools/explorer/ "
            "(select your app; grant pages_manage_posts, pages_read_engagement).",
            file=sys.stderr,
        )
    sys.exit(1)


def exchange_for_long_lived(app_id: str, app_secret: str, short_token: str) -> str:
    result = graph_get(
        f"{GRAPH_URL}/oauth/access_token",
        {
            "grant_type": "fb_exchange_token",
            "client_id": app_id,
            "client_secret": app_secret,
            "fb_exchange_token": short_token,
        },
    )
    return result["access_token"]


def fetch_pages(user_token: str, app_secret: str) -> list[dict]:
    pages: list[dict] = []
    url = f"{GRAPH_URL}/me/accounts"
    # appsecret_proof is required if the app has "Require App Secret" enabled,
    # and harmless otherwise
    params = {
        "access_token": user_token,
        "appsecret_proof": appsecret_proof(user_token, app_secret),
    }
    while url:
        result = graph_get(url, params)
        pages.extend(result.get("data", []))
        url = result.get("paging", {}).get("next", "")
        params = {}  # paging.next already carries the full query string
    return pages


def debug_token(token: str, app_id: str, app_secret: str) -> dict:
    result = graph_get(
        f"{GRAPH_URL}/debug_token",
        {"input_token": token, "access_token": f"{app_id}|{app_secret}"},
    )
    return result["data"]


def main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "short_lived_token",
        help="Short-lived user token from the Graph API Explorer",
    )
    parser.add_argument(
        "--app-id",
        default=settings.facebook_app_id,
        help="Facebook App ID (default: FACEBOOK_APP_ID from .env)",
    )
    parser.add_argument(
        "--app-secret",
        default=settings.facebook_app_secret,
        help="Facebook App Secret (default: FACEBOOK_APP_SECRET from .env)",
    )
    parser.add_argument(
        "--page-id", default="", help="Only print the token for this page ID"
    )
    args = parser.parse_args()

    if not args.app_id or not args.app_secret:
        parser.error(
            f"--app-id and --app-secret are required (or set them in .env). {APP_SECRET_HELP}"
        )

    print("Exchanging short-lived token for a long-lived user token...")
    long_lived = exchange_for_long_lived(
        args.app_id, args.app_secret, args.short_lived_token
    )

    print("Fetching page access tokens...")
    pages = fetch_pages(long_lived, args.app_secret)
    if args.page_id:
        pages = [page for page in pages if page.get("id") == args.page_id]
    if not pages:
        print(
            "No pages returned. Ensure the token has pages_read_engagement and "
            "your user has a role on the target page.",
            file=sys.stderr,
        )
        sys.exit(1)

    for page in pages:
        token = page["access_token"]
        info = debug_token(token, args.app_id, args.app_secret)
        expires_at = info.get("expires_at", 0)
        if expires_at == 0:
            expires = "never expires"
        else:
            expires_dt = datetime.fromtimestamp(expires_at, tz=timezone.utc)
            expires = f"expires {expires_dt:%Y-%m-%d %H:%M UTC}"
        scopes = info.get("scopes", [])
        print(f"\nPage: {page.get('name')} (id {page['id']})")
        print(f"  Token: {token}")
        print(f"  Valid: {info.get('is_valid')} | {expires}")
        print(f"  Scopes: {', '.join(scopes)}")
        if "pages_manage_posts" not in scopes:
            print("  WARNING: pages_manage_posts missing — publishing will fail.")

    print(
        "\nPaste into backend/.env:\n"
        "  FACEBOOK_ACCESS_TOKEN=<page token>\n"
        f"  FACEBOOK_APP_ID={args.app_id}  # enables the startup token check\n"
        "  FACEBOOK_APP_SECRET=<app secret>\n"
        "E2E tests reuse this token automatically; they only need\n"
        "  E2E_FACEBOOK_PAGE_ID=<page id>  in backend/tests/e2e/.env.e2e"
    )


if __name__ == "__main__":
    main()
