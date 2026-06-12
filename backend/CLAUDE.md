# Campaign Planner Backend - Claude Guidelines

## Build & Development
- Development server: `poetry run uvicorn app.main:app --reload`
- Run tests: `poetry run pytest`
- Run integration tests: `poetry run pytest tests/integration/ -v`
- Format code: `poetry run black .`
- Lint: `poetry run ruff check .`
- Pre-commit: `poetry run pre-commit run --all-files`

## Code Style
- Follow PEP 8 standards
- Use type hints for all functions
- Docstrings for public functions and classes
- 4-space indentation (Python standard)
- **Line length limit: 100 characters (enforced by ruff)**
  - Break long lines using intermediate variables or string concatenation
  - Use parentheses for natural line breaks in expressions

## Architecture
- API routes in `app/features/*/routes.py`
- Business logic in `app/features/*/service.py`
- Publishers in `app/features/publishing/publishers/`
- Shared utilities in `app/common/`
- Storage service in `app/common/storage/`

## AI Provider Abstraction
All text generation must go through `ProviderFactory` in `app/common/ai_providers` — never import `anthropic`, `openai`, or any SDK directly in feature code.

**Pattern** (used in `CaptionGenerator` and `PromptGenerator`):
```python
from app.common.ai_providers import Message, ProviderFactory, TextGenerationRequest

class MyGenerator:
    def __init__(self, provider_name: str | None = None):
        self.provider = ProviderFactory.create(provider_name)

    def generate(self, ...):
        request = TextGenerationRequest(
            messages=[
                Message(role="system", content=SYSTEM_PROMPT),
                Message(role="user", content=user_prompt),
            ],
            model=None,   # uses provider default; set explicitly to override
            temperature=0.7,
            max_tokens=500,
        )
        response = self.provider.generate(request)
        # response.text, response.provider, response.model available
```

- Provider is selected via the `TEXT_GENERATION_PROVIDER` env var (defaults configured in settings)
- Retry logic is handled inside the provider — do not add `tenacity` decorators on top
- Pass `provider_name` to `__init__` to allow per-call overrides in tests or special cases

## Testing Guidelines
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- E2E tests in `tests/e2e/`
- Use mock publishers for testing (see `tests/mocks/`)
- Always run tests before committing

### Test Data Organization
- **All test data must be colocated with the test type it belongs to**
- Integration test data: `tests/integration/data/`, `tests/integration/fixtures/`
- E2E test data: `tests/e2e/data/`, `tests/e2e/fixtures/`
- Unit test data: `tests/unit/fixtures/`
- Shared mocks: `tests/mocks/`
- Never mix test data from different test types

## Pre-commit Workflow
⚠️ **CRITICAL: ALWAYS run pre-commit hooks before any code changes are complete**

### Before Committing
1. **Run pre-commit**: `poetry run pre-commit run --all-files`
2. **Fix all linting issues** (especially line length violations)
3. **Run tests**: `poetry run pytest`
4. **Only commit after all checks pass**

### Common Pre-commit Failures
- **E501 Line too long**: Lines must be ≤100 characters
  - Fix: Break long lines using intermediate variables
  - Example: Instead of `long_var = f"{foo['bar']}-{baz['qux'].lower().replace(' ', '-')}"`
  - Use: `temp = baz['qux'].lower().replace(' ', '-')` then `long_var = f"{foo['bar']}-{temp}"`
- **Import sorting**: Use ruff to auto-fix import order
- **Trailing whitespace**: Remove all trailing spaces

## Git Workflow
- Feature branches: `feature/<name>/description`
- Create PRs to main branch for review
- Descriptive commit messages
- Include Co-Authored-By for pair programming
