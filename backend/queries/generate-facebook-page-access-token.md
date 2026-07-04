# How to Generate a Long-Lived Facebook Page Access Token

This guide walks through minting a **never-expiring Facebook Page access token** from your
Facebook App ID, App Secret, and a short-lived user token. The publisher flow
(`app/features/publishing/publishers/facebook.py`) reads this token from
`settings.facebook_access_token` and sends it as the `access_token` field on every Graph API
call. The E2E tests reuse the same token (see [Step 4](#step-4--where-to-put-the-token)).

All Graph API calls use version **v21.0** (`facebook_api_version` in `app/core/config.py`).

## Overview

There are three kinds of Meta token:

| Token | Lifetime |
|-------|----------|
| Short-lived **User** token (Graph API Explorer) | ~1–2 hours |
| Long-lived **User** token | ~60 days |
| **Page** token derived from a long-lived user token | **Never expires** |

A Page token minted from a long-lived user token has `expires_at: 0` — Meta only invalidates
it on password change, permission revocation, or ~90 days of user inactivity on the app. This
is the credential you want. The chain is:

```
short-lived user token  ->  long-lived user token  ->  Page access token
```

## Prerequisites

- A Facebook App — you need its **App ID** and **App Secret**.
- An admin/editor role on the target Facebook **Page**.
- A short-lived **user** token (obtained in Step 2).

## Step 1 — Get the App ID & App Secret

1. Go to <https://developers.facebook.com/apps> and select your app.
2. Navigate to **App settings → Basic**.
3. The **App ID** is shown at the top. Click **Show** next to **App Secret** and copy it.

Keep the App Secret private — never commit it.

## Step 2 — Get a short-lived user token

1. Open the Graph API Explorer: <https://developers.facebook.com/tools/explorer/>
2. In the top-right, select your **app** from the *Meta App* dropdown.
3. Under **Permissions**, add both:
   - `pages_manage_posts`
   - `pages_read_engagement`
4. Click **Generate Access Token** and approve the dialog (select the target Page when asked).
5. Copy the generated token. This short-lived token expires within a couple of hours — use it
   promptly in Step 3.

## Step 3 — Mint the Page access token

You can either run the helper script (recommended) or make the Graph API calls by hand.

### Path A (recommended) — helper script

From the `backend/` directory:

```bash
poetry run python get_facebook_page_token.py <short-lived-token> \
    --app-id <app-id> --app-secret <app-secret>
```

- `--app-id` / `--app-secret` default to `FACEBOOK_APP_ID` / `FACEBOOK_APP_SECRET` from `.env`,
  so you can omit them once those are set.
- Add `--page-id <page-id>` to print only the token for one specific Page.

The script exchanges the short-lived token for a long-lived user token, fetches every Page you
manage, and prints — for each Page — the **Page access token**, whether it is valid, its expiry
(`never expires` for a correctly minted token), and its granted scopes. It warns if
`pages_manage_posts` is missing (publishing would fail).

### Path B — manual Graph API calls

These mirror exactly what the script does. Substitute your real values.

1. **Exchange the short-lived user token for a long-lived user token:**

   ```
   GET https://graph.facebook.com/v21.0/oauth/access_token?grant_type=fb_exchange_token&client_id={app_id}&client_secret={app_secret}&fb_exchange_token={short_lived_token}
   ```

   The response contains the long-lived user token in `access_token`.

2. **List your Pages and their Page tokens** (each entry's `access_token` is a Page token):

   ```
   GET https://graph.facebook.com/v21.0/me/accounts?access_token={long_lived_user_token}
   ```

   Or fetch a single Page's token directly:

   ```
   GET https://graph.facebook.com/v21.0/{page_id}?fields=access_token&access_token={long_lived_user_token}
   ```

3. **Verify it never expires** (`expires_at: 0`) and has the right scopes:

   ```
   GET https://graph.facebook.com/v21.0/debug_token?input_token={page_token}&access_token={app_id}|{app_secret}
   ```

   Confirm the response shows `"is_valid": true`, `"expires_at": 0`, and `pages_manage_posts`
   in `scopes`.

## Step 4 — Where to put the token

### App runtime (`backend/.env`)

```dotenv
FACEBOOK_ACCESS_TOKEN=<page token>
FACEBOOK_APP_ID=<app id>
FACEBOOK_APP_SECRET=<app secret>
```

Setting `FACEBOOK_APP_ID` and `FACEBOOK_APP_SECRET` also enables the startup token health
check (`check_facebook_token_health` in `app/features/publishing/utils.py`), which calls
`debug_token` and warns early if the token is invalid or nearing expiry.

### E2E tests (`backend/tests/e2e/.env.e2e`)

The E2E suite reuses the app's token automatically — you only need the Page ID:

```dotenv
RUN_E2E=1
E2E_FACEBOOK_PAGE_ID=<page id>
```

`E2E_FACEBOOK_ACCESS_TOKEN` is optional; when unset it falls back to `FACEBOOK_ACCESS_TOKEN`
from `backend/.env` (see `tests/e2e/conftest.py`).

## Verify end to end

- Run the E2E publisher tests (they publish to the real Page):

  ```bash
  RUN_E2E=1 poetry run pytest -m e2e tests/e2e/ -v
  ```

- Or hit the `debug_token` endpoint from Step 3 and confirm `"is_valid": true`,
  `"expires_at": 0`, and `pages_manage_posts` in the scopes.

## Troubleshooting

| Symptom | Cause / fix |
|---------|-------------|
| `OAuthException code 190` (often subcode 463) | Token invalid or expired. Get a fresh short-lived token from the Graph API Explorer and redo Step 3. |
| Empty Pages list from `/me/accounts` | The token lacks `pages_read_engagement`, or your user has no role on the target Page. |
| `pages_manage_posts` missing from scopes | Re-generate the user token in Step 2 with that permission granted — publishing will fail without it. |
