# E2E Publisher Flow Tests

⚠️ **WARNING: These tests publish to REAL social media accounts!**

This directory contains end-to-end tests that verify the complete publishing workflow by publishing to **actual** Facebook and Instagram accounts. Posts will be publicly visible and must be manually deleted after testing.

## Overview

The E2E tests use the actual `PublisherService` with real `FacebookPublisher` and `InstagramPublisher` implementations (no mocks). They verify:

- ✅ Publishing to a real Facebook Page
- ✅ Publishing to a real Instagram Business Account
- ✅ Publishing to both platforms simultaneously
- ✅ Image URL handling for Instagram (via Facebook-hosted images)
- ✅ Metadata status updates
- ✅ Error handling with actual APIs

## Prerequisites

Before running E2E tests, you need:

1. **Facebook Page** - A Facebook Page you control
2. **Instagram Business Account** - Connected to your Facebook Page
3. **Facebook Access Token** - With permissions: `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`
4. **Instagram Access Token** - With permissions: `instagram_basic`, `instagram_content_publish`

## Setup Instructions

### Step 1: Configure E2E Credentials

Copy the example environment file:

```bash
cp tests/e2e/.env.e2e.example tests/e2e/.env.e2e
```

### Step 2: Update Your Credentials

⚠️ **This is the ONLY file you need to edit!**

Open `tests/e2e/.env.e2e` and update these 5 values:

| What to Update | File Location | Variable Name | How to Get It |
|----------------|---------------|---------------|---------------|
| **Enable E2E Tests** | `tests/e2e/.env.e2e` | `RUN_E2E` | Set to `1` to enable, `0` to disable |
| Facebook Page ID | `tests/e2e/.env.e2e` | `E2E_FACEBOOK_PAGE_ID` | See "Getting Facebook Page ID" below |
| Facebook Access Token | `tests/e2e/.env.e2e` | `E2E_FACEBOOK_ACCESS_TOKEN` | See "Getting Access Tokens" below |
| Instagram Account ID | `tests/e2e/.env.e2e` | `E2E_INSTAGRAM_ACCOUNT_ID` | See "Getting Instagram Account ID" below |
| Instagram Access Token | `tests/e2e/.env.e2e` | `E2E_INSTAGRAM_ACCESS_TOKEN` | See "Getting Access Tokens" below |

**Example `.env.e2e` (with your real values):**
```bash
RUN_E2E=1  # Set to 1 to enable E2E tests
E2E_FACEBOOK_PAGE_ID=123456789012345
E2E_FACEBOOK_ACCESS_TOKEN=EAABsbCS...very_long_token...ZD
E2E_INSTAGRAM_ACCOUNT_ID=17841405309211844
E2E_INSTAGRAM_ACCESS_TOKEN=EAABsbCS...very_long_token...ZD
```

**Important:** E2E tests will only run when `RUN_E2E=1`. This prevents accidental execution of tests that publish to real social media accounts.

### Getting Facebook Page ID

1. Go to your Facebook Page
2. Click **About** in the left sidebar
3. Scroll down to find **Page ID**
4. Copy the numeric ID (e.g., `123456789012345`)

**Alternative method:**
1. Visit your Facebook Page
2. Look at the URL: `facebook.com/YourPageName-123456789012345`
3. The numbers at the end are your Page ID

### Getting Instagram Account ID

Use the Facebook Graph API Explorer:

1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your app (or create one if needed)
3. Request permissions: `instagram_basic`, `pages_show_list`
4. Make this query:
   ```
   GET /me/accounts?fields=instagram_business_account{id}
   ```
5. Look for your Page in the response, copy the `instagram_business_account.id` value

**Example response:**
```json
{
  "data": [
    {
      "instagram_business_account": {
        "id": "17841405309211844"  ← This is your Instagram Account ID
      }
    }
  ]
}
```

### Getting Access Tokens

#### Option 1: Graph API Explorer (Quick, Temporary Tokens)

1. Go to [Graph API Explorer](https://developers.facebook.com/tools/explorer/)
2. Select your Facebook App
3. Click **Permissions** and add:
   - For Facebook: `pages_show_list`, `pages_read_engagement`, `pages_manage_posts`
   - For Instagram: `instagram_basic`, `instagram_content_publish`
4. Click **Generate Access Token**
5. Copy the token

⚠️ **Note:** These tokens expire in 1-2 hours. For longer testing sessions, use Option 2.

#### Option 2: Long-Lived Tokens (Recommended)

1. Generate a short-lived token using Option 1
2. Exchange it for a long-lived token (60 days):
   ```bash
   curl -X GET "https://graph.facebook.com/v22.0/oauth/access_token?grant_type=fb_exchange_token&client_id=YOUR_APP_ID&client_secret=YOUR_APP_SECRET&fb_exchange_token=SHORT_LIVED_TOKEN"
   ```
3. Use the returned `access_token` in your `.env.e2e`

📚 **Learn more:** [Facebook Access Token Documentation](https://developers.facebook.com/docs/facebook-login/guides/access-tokens)

## Instagram Image URL Handling

Instagram requires publicly accessible image URLs for publishing. **The E2E tests handle this automatically:**

1. **Upload to Facebook first** - Test publishes image to Facebook Page
2. **Fetch the image URL** - Makes Graph API call to get the FB-hosted image URL
3. **Publish to Instagram** - Uses the FB-hosted URL for Instagram post

**You don't need to set up any image hosting service!** The tests handle this workflow automatically.

## Running E2E Tests

### Run All E2E Tests

```bash
poetry run pytest tests/e2e/ -m e2e -v
```

### Run Specific Test

```bash
# Facebook only
poetry run pytest tests/e2e/test_publisher_flow_e2e.py::TestPublisherFlowE2E::test_publish_to_facebook_real -v

# Instagram only
poetry run pytest tests/e2e/test_publisher_flow_e2e.py::TestPublisherFlowE2E::test_publish_to_instagram_real -v

# Multi-platform
poetry run pytest tests/e2e/test_publisher_flow_e2e.py::TestPublisherFlowE2E::test_publish_multi_platform_real -v
```

### Skip E2E Tests (Default Behavior)

E2E tests are automatically skipped when:
- `RUN_E2E` is not set to `1` in `.env.e2e` (default)
- Credentials are missing or incomplete

```bash
poetry run pytest  # E2E tests skipped if RUN_E2E≠1 or credentials missing
```

**To disable E2E tests**, set `RUN_E2E=0` in `.env.e2e` or remove the variable entirely.

### Automatic Sample Data Generation

E2E tests automatically generate fresh sample data before each test run. You don't need to manually run the `generate_sample_data.py` script. The tests handle this automatically to ensure clean, consistent test data.

## Expected Results

When tests pass, you'll see:

✅ Console output with post IDs:
```
✅ Successfully published to Facebook!
   Post ID: 123456789012345_67890
   ⚠️  Remember to delete this test post from your Facebook Page!
```

✅ **Actual posts on your social media accounts**:
- Visit your Facebook Page to see the test post
- Visit your Instagram account to see the test post
- Posts will have the caption: "🧪 This is an E2E test post. You can safely delete this after testing."

## Post-Test Cleanup

⚠️ **IMPORTANT: Tests do NOT automatically delete posts!**

After verification, manually delete test posts:

1. **Facebook:**
   - Go to your Facebook Page
   - Find the test post (look for "🧪 E2E test" caption)
   - Click ⋯ (three dots) → Delete

2. **Instagram:**
   - Open Instagram app or web
   - Find the test post on your business account
   - Click ⋯ (three dots) → Delete

## Troubleshooting

### Tests are Skipped

**Problem:** Tests show "skipped" status

**Solution:**
- Verify `RUN_E2E=1` is set in `tests/e2e/.env.e2e`
- Verify `.env.e2e` exists in `tests/e2e/`
- Check all 4 credentials are set (no empty values)
- Ensure no typos in variable names

### "Missing E2E credentials" Error

**Problem:** `ValueError: Missing E2E credentials: facebook_page_id, ...`

**Solution:**
1. Verify `.env.e2e` exists and is in the correct location
2. Check that all 4 variables are set with actual values
3. Ensure no extra spaces around `=` in the `.env.e2e` file

### Facebook Publishing Fails

**Problem:** `Facebook API error: 403` or `190` (invalid token)

**Solutions:**
- Verify your access token is valid (test in Graph API Explorer)
- Check token has required permissions: `pages_manage_posts`
- Ensure token hasn't expired (regenerate if needed)
- Verify Page ID is correct (numeric ID, not username)

### Instagram Publishing Fails

**Problem:** `Failed to create media container` or `400` error

**Solutions:**
- Verify Instagram Account ID is correct (should be 17+ digits)
- Check access token has `instagram_content_publish` permission
- Ensure your Instagram account is a Business Account (not Personal)
- Verify it's connected to your Facebook Page
- Check image URL is publicly accessible (test uploading to FB first)

### "No Facebook page ID configured" Error

**Problem:** Test fails with "No Facebook page ID configured"

**Solution:**
- Check that `E2E_FACEBOOK_PAGE_ID` is set in `.env.e2e`
- Verify the Page ID is numeric (not the page username)
- Ensure no quotes around the value in `.env.e2e`

### Image File Not Found

**Problem:** `FileNotFoundError: Image not found`

**Solution:**
1. Run the data generation script:
   ```bash
   python3 tests/e2e/generate_sample_data.py
   ```
2. Verify the file exists:
   ```bash
   ls tests/e2e/data/campaigns/generated/sample-e2e-campaign/image.jpg
   ```

### Rate Limiting

**Problem:** `429 Too Many Requests` error

**Solution:**
- Wait a few minutes before retrying
- Avoid running tests too frequently
- Check Facebook API rate limits in Developer Console

## File Structure

```
backend/tests/e2e/
├── __init__.py                                    # Empty init file
├── conftest.py                                    # E2E fixtures (loads .env.e2e)
├── test_publisher_flow_e2e.py                    # Main E2E tests
├── .env.e2e.example                              # Template (committed to git)
├── .env.e2e                                      # Your credentials (gitignored)
├── README.md                                     # This file
├── generate_sample_data.py                       # Sample data generator script
└── data/
    └── campaigns/
        └── generated/
            └── sample-e2e-campaign/
                ├── metadata.json                 # Pre-generated metadata
                └── image.jpg                     # Test image (1080x1080)
```

## Important Notes

- **Never commit `.env.e2e`** - It contains real credentials and is gitignored
- **Tests publish to real accounts** - Always manually verify and delete test posts
- **Tokens expire** - You may need to regenerate access tokens periodically
- **Instagram requires Business Account** - Personal accounts won't work
- **No mocks** - These tests use actual API calls (costs apply if rate limits exceeded)

## Additional Resources

- [Facebook Graph API Documentation](https://developers.facebook.com/docs/graph-api)
- [Instagram Graph API Documentation](https://developers.facebook.com/docs/instagram-api)
- [Facebook Access Tokens Guide](https://developers.facebook.com/docs/facebook-login/guides/access-tokens)
- [Instagram Publishing API](https://developers.facebook.com/docs/instagram-api/guides/content-publishing)

---

**Questions or Issues?**

If you encounter issues not covered in the troubleshooting section, check:
1. Facebook Developer Console for API errors
2. Graph API Explorer to test queries manually
3. Project documentation in `backend/CLAUDE.md`
