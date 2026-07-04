# How to Generate a Long-Lived Instagram Access Token

The Instagram publisher (`app/features/publishing/publishers/instagram.py`) reads the token
from `settings.instagram_access_token` and the account ID from `campaign.instagram_account_id`.
All Graph API calls use version **v21.0**.

---

## Token types

| Token | Lifetime |
|-------|----------|
| Short-lived user token (Graph API Explorer) | ~1–2 hours |
| Long-lived user token | ~60 days |

> **Note:** Unlike Facebook Page tokens, there is no never-expiring Instagram token.
> You must refresh the long-lived token before it expires by re-running the script
> with a fresh short-lived token.

---

## Prerequisites

- Facebook App (App ID + App Secret) — the same app used for Facebook publishing
- An **Instagram Business** or **Creator** account linked to a Facebook Page
  (link at: Facebook Page → Settings → Linked Accounts → Instagram)
- Your Facebook user must have admin or editor role on that Page
- A short-lived user token with the following permissions:
  - `instagram_basic`
  - `instagram_content_publish`
  - `pages_show_list`
  - `pages_read_engagement`

---

## Steps

### Path A — Script (recommended)

```bash
cd backend
poetry run python get_instagram_access_token.py <short-lived-token> \
    --app-id <app-id> --app-secret <app-secret>
```

`--app-id` / `--app-secret` default to `FACEBOOK_APP_ID` / `FACEBOOK_APP_SECRET` from `.env`.

The script outputs the long-lived user token and your Instagram Business Account ID.

### Path B — Manual Graph API calls

**1. Get App ID & App Secret**

`https://developers.facebook.com/apps` → your app → App settings → Basic → App Secret → Show.

**2. Get a short-lived user token**

`https://developers.facebook.com/tools/explorer/` → select your app → add the four
permissions above → Generate Access Token.

**3. Exchange for a long-lived user token (~60 days)**

```
GET https://graph.facebook.com/v21.0/oauth/access_token
  ?grant_type=fb_exchange_token
  &client_id=<app-id>
  &client_secret=<app-secret>
  &fb_exchange_token=<short-lived-token>
```

Save the returned `access_token` — this is your `INSTAGRAM_ACCESS_TOKEN`.

**4. Find your Instagram Business Account ID**

```
GET https://graph.facebook.com/v21.0/me/accounts
  ?access_token=<long-lived-token>
```

Pick your Page from the list and note its `id`. Then:

```
GET https://graph.facebook.com/v21.0/<page-id>
  ?fields=instagram_business_account
  &access_token=<page-access-token>
```

The `instagram_business_account.id` in the response is your `E2E_INSTAGRAM_ACCOUNT_ID`.

---

## Where to put the credentials

**Runtime** (`backend/.env`):

```
INSTAGRAM_ACCESS_TOKEN=<long-lived user token>
```

**E2E tests** (`backend/tests/e2e/.env.e2e`):

```
E2E_INSTAGRAM_ACCOUNT_ID=<instagram business account id>
# E2E_INSTAGRAM_ACCESS_TOKEN=   (optional — falls back to INSTAGRAM_ACCESS_TOKEN above)
RUN_E2E=1
```

Then run the E2E tests:

```bash
cd backend
poetry run pytest tests/e2e/ -m e2e -v -k "instagram"
```

---

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| OAuthException code 190 / 463 | Token expired — get a fresh short-lived token and re-run |
| Empty `/me/accounts` | Missing `pages_show_list` permission, or no Page role |
| No Instagram account found on page | Link an Instagram Business/Creator account to the Page in Page Settings |
| Missing `instagram_content_publish` | Re-generate token with all four permissions in the Explorer |
| `(#200) The user hasn't authorized the application` | App is not approved for `instagram_content_publish` — submit for review or use a test user |
