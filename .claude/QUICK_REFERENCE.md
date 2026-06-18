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
# Image: backend/app/features/generation/image.py
# Prompts: backend/app/features/generation/prompt.py
```

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
  "tone": "professional|casual|friendly",
  "brand_colors": ["#HEX1", "#HEX2"],
  "social": {
    "facebook_page_id": "",
    "instagram_account_id": ""
  }
}
```

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
poetry run uvicorn app.main:app --reload   # Start server
poetry run pytest                          # Run tests
poetry run black .                         # Format code
poetry run ruff check .                    # Lint code
poetry run pre-commit run --all-files      # All checks
```

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
