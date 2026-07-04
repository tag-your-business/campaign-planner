#!/usr/bin/env python3
"""
Find your Instagram Business Account ID and mint a long-lived access token.

Instagram uses the same Facebook Graph API (same App ID and App Secret).
Unlike Facebook Page tokens, Instagram tokens are long-lived user tokens (~60 days)
— there is no never-expiring equivalent. Refresh the token before it expires by
re-running this script with a fresh short-lived token.

Steps:
    1. Reveal your App Secret: https://developers.facebook.com/apps
       -> your app -> App settings -> Basic -> App Secret -> Show.
    2. Get a short-lived user token from
       https://developers.facebook.com/tools/explorer/ (select your app,
       grant instagram_basic, instagram_content_publish,
       pages_show_list, pages_read_engagement).
    3. Run from the backend directory:
       poetry run python get_instagram_access_token.py <short-lived-token> \\
           --app-id <app-id> --app-secret <app-secret>

--app-id / --app-secret default to FACEBOOK_APP_ID / FACEBOOK_APP_SECRET
from .env when set there.
"""

import argparse
import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.core.config import settings  # noqa: E402
from get_facebook_page_token import (  # noqa: E402
    APP_SECRET_HELP,
    GRAPH_URL,
    exchange_for_long_lived,
    fetch_pages,
    graph_get,
)


def fetch_instagram_account(page_id: str, page_token: str) -> str | None:
    """Return the Instagram Business Account ID linked to a Facebook Page, or None."""
    result = graph_get(
        f"{GRAPH_URL}/{page_id}",
        {"fields": "instagram_business_account", "access_token": page_token},
    )
    return result.get("instagram_business_account", {}).get("id")


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
    args = parser.parse_args()

    if not args.app_id or not args.app_secret:
        parser.error(
            f"--app-id and --app-secret are required (or set them in .env). {APP_SECRET_HELP}"
        )

    print("Exchanging short-lived token for a long-lived user token...")
    long_lived = exchange_for_long_lived(
        args.app_id, args.app_secret, args.short_lived_token
    )
    print(f"Long-lived user token (~60 days): {long_lived}")

    print("\nFetching Facebook Pages to find linked Instagram Business Accounts...")
    pages = fetch_pages(long_lived, args.app_secret)
    if not pages:
        print(
            "No pages returned. Ensure the token has pages_show_list / pages_read_engagement "
            "and your user has a role on the target page.",
            file=sys.stderr,
        )
        sys.exit(1)

    found = []
    for page in pages:
        ig_id = fetch_instagram_account(page["id"], page["access_token"])
        status = (
            f"Instagram account: {ig_id}" if ig_id else "no linked Instagram account"
        )
        print(f"  Page: {page.get('name')} (id {page['id']}) — {status}")
        if ig_id:
            found.append((page, ig_id))

    if not found:
        print(
            "\nNo Instagram Business Accounts found. "
            "Ensure at least one Facebook Page has a linked Instagram Business (or Creator) "
            "account. Link it at: https://www.facebook.com/pages/ -> your page -> "
            "Settings -> Linked Accounts -> Instagram.",
            file=sys.stderr,
        )
        sys.exit(1)

    print("\n" + "=" * 60)
    for page, ig_id in found:
        print(f"\nPage: {page.get('name')} (id {page['id']})")
        print(f"  Instagram Business Account ID: {ig_id}")

    print(
        "\nPaste into backend/.env:\n"
        f"  INSTAGRAM_ACCESS_TOKEN=<long-lived user token above>\n"
        "\nPaste into backend/tests/e2e/.env.e2e:\n"
        f"  E2E_INSTAGRAM_ACCOUNT_ID={found[0][1]}\n"
        "  # E2E_INSTAGRAM_ACCESS_TOKEN=  (optional — falls back to INSTAGRAM_ACCESS_TOKEN)\n"
        "\nThe long-lived user token expires in ~60 days. Re-run this script with a "
        "fresh short-lived token to renew it."
    )


if __name__ == "__main__":
    main()
