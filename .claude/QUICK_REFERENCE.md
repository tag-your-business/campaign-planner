# Quick Reference for AI Assistants

This is a condensed reference for AI assistants working with this codebase. For comprehensive details, see `PROJECT_CONTEXT.md`.

## Essential Paths

```
backend/app/
├── core/config.py           # All settings & env vars
├── features/
│   ├── companies/service.py  # Company profile operations
│   ├── events/service.py     # Event calendar operations
│   ├── generation/
│   │   ├── branding/         # Pillow overlay renderer
│   │   │   ├── config.py     #   LayoutConfig — ALL visual tuning lives here
│   │   │   ├── colors.py     #   background-aware text color helpers
│   │   │   ├── elements.py   #   render_logo / render_contact_block / render_banner
│   │   │   ├── fonts.py      #   font priority list
│   │   │   ├── layout.py     #   slot geometry + collision resolver
│   │   │   └── service.py    #   BrandingService.apply()
│   │   ├── caption.py        # GPT caption generation
│   │   ├── image.py          # gpt-image-2 image generation
│   │   └── planner.py        # Campaign planning logic
│   └── publishing/
│       └── publishers/       # Social media integrations
└── main.py                   # FastAPI app entry point

backend/data/
├── companies/{slug}/profile.json  # Company branding & settings
├── events/{year}.json             # Event calendar
└── campaigns/{slug}/{id}/         # Generated campaigns
```

## Common Tasks

### Read Company Profile
```python
# Location: backend/data/companies/{company_slug}/profile.json
# Structure: slug, name, industry, tone, brand_colors, social
```

### Add New Event
```python
# Edit: backend/data/events/2026.json
# Add: {"date": "YYYY-MM-DD", "name": "...", "description": "...", "tags": [...]}
```

### Modify Generation Logic
```python
# Caption: backend/app/features/generation/caption.py
# Image:   backend/app/features/generation/image.py
# Prompts: backend/app/features/generation/prompt.py
```

### Tune Branding Visuals
```python
# ALL visual constants: backend/app/features/generation/branding/config.py
# Key fields in LayoutConfig:
#   h_pad_frac       — horizontal padding inside pills
#   v_pad_top_frac   — top padding inside pills
#   v_pad_bot_frac   — bottom padding inside pills (can differ from top)
#   banner_font_frac / contact_font_frac — font size as fraction of image width
#   banner_border_frac — border thickness
#   banner_color / scrim_color — fill RGBA for banner / contact block
#   dynamic_text_color — True = auto-pick black/white text for contrast
```

### Add a New Banner / Contact Field
```python
# 1. Add value to contact_info in data/companies/{slug}/profile.json
# 2. Append key name to banner_fields or contact_fields in the branding block
# No code change required.
```

### Add / Run Prompt Evaluations
```
backend/tests/prompt/
├── framework/         # Shared engine (config_loader, evaluator, comparison)
│   ├── providers.yaml # Global model registry — add new providers here
│   └── metrics.yaml   # Global metrics registry
├── caption/           # Caption evals — prompts: prompt_v1/v2/v3.yaml
├── image/             # Image evals — prompts: prompt_auto_v{1,2}_gpt-5-4-mini_case{1,2,3}.yaml
└── image_prompt/      # Combined evals — prompt_v1/v2 + case variants
```
- Each eval directory has its own `config.yaml` and `data/campaign_specs.json`
- Add new prompt variant: create a `prompts/prompt_vN.yaml` in the relevant directory
- Add new case: create `prompt_auto_v{N}_gpt-5-4-mini_case{N}.yaml` for image/image_prompt evals

### Add Environment Variable
```python
# 1. Add to: backend/app/core/config.py (Settings class)
# 2. Add to: backend/.env.example
# 3. Update: .claude/PROJECT_CONTEXT.md
```

## File Reading Priority

When exploring, read in this order:
1. `backend/app/core/config.py` - Understand available settings
2. Feature service you're working on (`features/{feature}/service.py`)
3. Related models (`features/{feature}/models.py` if exists)
4. Test files to understand expected behavior

## Key Configuration

```python
# backend/app/core/config.py
settings.openai_api_key         # OpenAI API key
settings.data_dir               # Data directory path
settings.companies_dir          # Companies data path
settings.events_dir             # Events data path
settings.generate_cron          # Generation schedule
settings.publish_cron           # Publishing schedule
```

## Data Schemas

### Company Profile
```json
{
  "slug": "company_id",
  "name": "Company Name",
  "industry": "industry_type",
  "tone_keywords": ["warm", "trustworthy"],
  "brand_colors": { "primary": "#HEX1", "accent": "#HEX2" },
  "locations": [{ "city": "...", "state": "...", "country": "...", "is_primary": true }],
  "contact_info": {
    "email": "hello@example.com",
    "website": "www.example.com",
    "address": "...",
    "phone": "..."
  },
  "branding": {
    "logo_position": "top-left",
    "contact_position": "top-right",
    "contact_fields": ["email"],
    "banner_fields": ["website", "address"]
  },
  "social": { "facebook_page_id": "", "instagram_account_id": "" }
}
```
Logo file: `data/companies/{slug}/logo.png` (PNG, transparent background)

### Event
```json
{
  "date": "YYYY-MM-DD",
  "name": "Event Name",
  "description": "Description",
  "tags": ["tag1", "tag2"]
}
```

## Running Commands

```bash
# From backend/ directory
poetry run uvicorn app.main:app --reload          # Start server
poetry run pytest                                 # Run tests (unit + integration)
poetry run pytest -m eval tests/prompt/           # Run prompt eval tests (DeepEval)
poetry run black .                                # Format code
poetry run ruff check .                           # Lint code
poetry run pre-commit run --all-files             # All checks
```

> **Prompt eval dependency conflict**: DeepEval requires `openai <2.0.0` but the app uses `>=2.41.0`. Run eval tests in a separate venv. See `backend/tests/prompt/README.md`.

## Important Notes

1. **Always read files before editing** - Never propose changes to code you haven't read
2. **JSON storage** - All data in JSON files, no database currently
3. **Async functions** - Use async/await for I/O operations
4. **Type hints** - Encouraged but not enforced
5. **Tests required** - Add tests for new features
6. **Pre-commit hooks** - Will run automatically on commit

## Common Patterns

### Loading Company
```python
from app.features.companies.service import CompanyService

service = CompanyService()
company = service.load_company("company_slug")
```

### Accessing Settings
```python
from app.core.config import settings

api_key = settings.openai_api_key
data_path = settings.data_dir
```

### Error Handling
```python
# Raise descriptive errors
raise ValueError(f"Company not found: {company_slug}")

# Log with context
logger.error(f"Failed to generate caption for {company_slug}", exc_info=True)
```

## Questions to Ask User

Before making changes:
- "Which company should this apply to?"
- "Should this be configurable via environment variables?"
- "Do you want tests for this feature?"
- "Should I update the documentation?"

## File Naming

- Python files: `snake_case.py`
- Classes: `PascalCase`
- Functions: `snake_case`
- Constants: `UPPER_SNAKE_CASE`
- Company slugs: `lowercase_with_underscores`

## Testing Quick Reference

```python
# Unit test example
import pytest

def test_function_name():
    """Test description."""
    # Arrange
    input_data = "test"

    # Act
    result = function(input_data)

    # Assert
    assert result == expected

# Async test example
@pytest.mark.asyncio
async def test_async_function():
    """Test async function."""
    result = await async_function()
    assert result is not None
```

## When Stuck

1. Check `PROJECT_CONTEXT.md` for detailed context
2. Read `ARCHITECTURE.md` for system design
3. Check `DEVELOPMENT.md` for development workflow
4. Look at existing code for patterns
5. Check test files for usage examples

## TODOs in Codebase

- `backend/app/main.py:12` - Start schedulers in lifespan
- `backend/app/main.py:14` - Shutdown schedulers in lifespan

These are known planned features.
