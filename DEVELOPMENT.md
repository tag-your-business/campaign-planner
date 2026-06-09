# Development Guide

This guide covers everything you need to know to develop and contribute to Campaign Planner.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Initial Setup](#initial-setup)
- [Development Workflow](#development-workflow)
- [Code Style and Standards](#code-style-and-standards)
- [Testing](#testing)
- [Common Development Tasks](#common-development-tasks)
- [Debugging](#debugging)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### Required
- **Python 3.13+**: The project uses modern Python features
- **Poetry**: Dependency management and virtual environments
  ```bash
  curl -sSL https://install.python-poetry.org | python3 -
  ```

### Recommended
- **VS Code** or **PyCharm**: IDE with Python support
- **Git**: Version control
- **OpenAI API Key**: For testing generation features

### Optional
- **Docker**: For containerized deployment (future)
- **make**: For convenient command shortcuts (future)

## Initial Setup

### 1. Clone the Repository
```bash
git clone <repository-url>
cd campaign-planner
```

### 2. Backend Setup

```bash
cd backend

# Install dependencies (creates .venv automatically)
poetry install

# For development dependencies (includes testing, linting tools)
poetry install --with dev
```

### 3. Environment Configuration

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and add your API keys
# Required:
OPENAI_API_KEY=sk-...

# Optional (for publishing features):
FACEBOOK_ACCESS_TOKEN=...
INSTAGRAM_ACCESS_TOKEN=...
```

### 4. Setup Pre-commit Hooks

```bash
# Install pre-commit hooks
poetry run pre-commit install

# Test pre-commit setup (optional)
poetry run pre-commit run --all-files
```

### 5. Verify Setup

```bash
# Activate virtual environment
poetry shell

# Run the application
uvicorn app.main:app --reload

# In another terminal, check health endpoint
curl http://localhost:8000/health
# Should return: {"status":"ok"}
```

## Development Workflow

### Daily Development

1. **Activate Virtual Environment**
   ```bash
   cd backend
   poetry shell
   ```

2. **Run Development Server**
   ```bash
   # With auto-reload
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```

3. **Access API Documentation**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

### Making Changes

1. **Create a Feature Branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make Your Changes**
   - Follow code style guidelines (see below)
   - Add tests for new features
   - Update documentation if needed

3. **Run Tests**
   ```bash
   # Run all tests
   poetry run pytest

   # Run with coverage
   poetry run pytest --cov=app --cov-report=html

   # Run specific test file
   poetry run pytest tests/unit/test_companies.py

   # Run specific test
   poetry run pytest tests/unit/test_companies.py::test_load_company
   ```

4. **Run Linters and Formatters**
   ```bash
   # Format code with Black
   poetry run black .

   # Lint with Ruff
   poetry run ruff check .

   # Auto-fix Ruff issues
   poetry run ruff check --fix .

   # Run all pre-commit checks
   poetry run pre-commit run --all-files
   ```

5. **Commit Your Changes**
   ```bash
   git add .
   git commit -m "feat: description of your changes"
   # Pre-commit hooks will run automatically
   ```

6. **Push and Create Pull Request**
   ```bash
   git push origin feature/your-feature-name
   # Create PR on GitHub
   ```

## Code Style and Standards

### Python Code Style

We follow these standards:
- **PEP 8** with some modifications
- **Black** for formatting (line length: 100)
- **Ruff** for linting
- **Type hints** encouraged but not mandatory

### Black Configuration
```toml
# In pyproject.toml
[tool.black]
line-length = 100
target-version = ['py313']
```

### Ruff Configuration
```toml
# In pyproject.toml
[tool.ruff]
line-length = 100

[tool.ruff.lint]
select = ["E", "F"]  # pycodestyle errors, pyflakes
```

### Code Organization

#### Feature Structure
```
features/
└── {feature_name}/
    ├── __init__.py      # Public API exports
    ├── service.py       # Business logic
    ├── models.py        # Pydantic models (if needed)
    └── utils.py         # Helper functions (if needed)
```

#### Import Order
```python
# 1. Standard library
import os
from datetime import datetime

# 2. Third-party
from fastapi import FastAPI
from pydantic import BaseModel

# 3. Local application
from app.core.config import settings
from app.features.companies.service import CompanyService
```

### Naming Conventions

- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions/Variables**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`

### Docstrings

Use Google-style docstrings for functions and classes:

```python
def generate_caption(company_slug: str, event_name: str) -> str:
    """Generate a social media caption for an event.

    Args:
        company_slug: The company identifier
        event_name: Name of the event

    Returns:
        Generated caption text

    Raises:
        ValueError: If company_slug is invalid
        OpenAIError: If API call fails
    """
    pass
```

## Testing

### Test Structure

```
tests/
├── unit/               # Unit tests (isolated, mocked)
│   ├── test_companies.py
│   ├── test_events.py
│   └── test_generation.py
└── integration/        # Integration tests (real files, APIs)
    ├── test_generation_flow.py
    └── test_publishing_flow.py
```

### Writing Tests

#### Unit Test Example
```python
import pytest
from app.features.companies.service import CompanyService

def test_load_company_success():
    """Test loading a valid company profile."""
    service = CompanyService()
    company = service.load_company("abc_dental")

    assert company.slug == "abc_dental"
    assert company.name == "ABC Dental"
    assert company.industry == "dental"

def test_load_company_not_found():
    """Test loading a non-existent company."""
    service = CompanyService()

    with pytest.raises(ValueError):
        service.load_company("nonexistent")
```

#### Async Test Example
```python
import pytest
from app.features.generation.caption import generate_caption

@pytest.mark.asyncio
async def test_generate_caption():
    """Test caption generation."""
    caption = await generate_caption(
        company_slug="abc_dental",
        event_name="World Oral Health Day"
    )

    assert len(caption) > 0
    assert "dental" in caption.lower()
```

### Running Tests

```bash
# All tests
poetry run pytest

# Specific directory
poetry run pytest tests/unit/

# With coverage
poetry run pytest --cov=app --cov-report=html
# Open htmlcov/index.html to view coverage

# Verbose output
poetry run pytest -v

# Stop on first failure
poetry run pytest -x

# Run tests matching pattern
poetry run pytest -k "caption"
```

### Test Fixtures

Create fixtures in `conftest.py`:

```python
# tests/conftest.py
import pytest
from app.features.companies.service import CompanyService

@pytest.fixture
def company_service():
    """Provide a CompanyService instance."""
    return CompanyService()

@pytest.fixture
def sample_company():
    """Provide sample company data."""
    return {
        "slug": "test_company",
        "name": "Test Company",
        "industry": "technology",
        "tone": "casual",
        "brand_colors": ["#FF0000", "#0000FF"]
    }
```

## Common Development Tasks

### Adding a New Company

1. Create company directory:
   ```bash
   mkdir -p backend/data/companies/new_company_slug
   ```

2. Create `profile.json`:
   ```json
   {
     "slug": "new_company_slug",
     "name": "Company Name",
     "industry": "industry_type",
     "tone": "professional",
     "brand_colors": ["#HEX1", "#HEX2"],
     "social": {
       "facebook_page_id": "",
       "instagram_account_id": ""
     }
   }
   ```

3. Register in `data/registry/company_registry.json`:
   ```json
   {
     "companies": [
       "new_company_slug"
     ]
   }
   ```

### Adding New Events

Edit `backend/data/events/2026.json`:
```json
[
  {
    "date": "2026-03-15",
    "name": "New Event",
    "description": "Event description",
    "tags": ["holiday"]
  }
]
```

### Adding a New Feature Module

1. Create feature directory:
   ```bash
   mkdir -p backend/app/features/new_feature
   ```

2. Create `__init__.py`:
   ```python
   """New feature module."""
   from .service import NewFeatureService

   __all__ = ["NewFeatureService"]
   ```

3. Create `service.py`:
   ```python
   """New feature service."""

   class NewFeatureService:
       """Service for new feature."""

       def __init__(self):
           """Initialize service."""
           pass
   ```

4. Add tests:
   ```bash
   touch backend/tests/unit/test_new_feature.py
   ```

### Adding API Endpoints

1. Create route file:
   ```python
   # backend/app/api/v1/routes/campaigns.py
   from fastapi import APIRouter

   router = APIRouter(prefix="/campaigns", tags=["campaigns"])

   @router.get("/")
   async def list_campaigns():
       """List all campaigns."""
       return {"campaigns": []}
   ```

2. Register in `app/api/v1/__init__.py`:
   ```python
   from fastapi import APIRouter
   from .routes import campaigns

   api_router = APIRouter()
   api_router.include_router(campaigns.router)
   ```

3. Include in main app:
   ```python
   # app/main.py
   from app.api.v1 import api_router

   app.include_router(api_router, prefix="/api/v1")
   ```

## Debugging

### VS Code Configuration

Create `.vscode/launch.json`:
```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "app.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "jinja": true,
      "cwd": "${workspaceFolder}/backend",
      "env": {
        "PYTHONPATH": "${workspaceFolder}/backend"
      }
    }
  ]
}
```

### Using Python Debugger

```python
# Add breakpoint in code
import pdb; pdb.set_trace()

# Or with breakpoint() in Python 3.7+
breakpoint()
```

### Logging

```python
import logging

logger = logging.getLogger(__name__)

logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.exception("Exception with traceback")
```

## Troubleshooting

### Poetry Issues

**Problem**: `poetry install` fails
```bash
# Clear cache
poetry cache clear pypi --all

# Remove lock file and reinstall
rm poetry.lock
poetry install
```

**Problem**: Wrong Python version
```bash
# Set specific Python version
poetry env use python3.13

# Check current environment
poetry env info
```

### Import Errors

**Problem**: Module not found
```bash
# Ensure you're in poetry shell
poetry shell

# Check PYTHONPATH
echo $PYTHONPATH

# Run from correct directory
cd backend
python -m app.main
```

### OpenAI API Issues

**Problem**: Rate limiting
- Implement exponential backoff
- Use lower rate limits in settings
- Cache responses during development

**Problem**: API key invalid
```bash
# Check .env file
cat backend/.env | grep OPENAI_API_KEY

# Test API key
python -c "from openai import OpenAI; client = OpenAI(); print(client.models.list())"
```

### Pre-commit Hook Failures

**Problem**: Black formatting fails
```bash
# Run Black manually
poetry run black .

# Skip hooks temporarily (not recommended)
git commit --no-verify
```

**Problem**: Ruff linting fails
```bash
# Auto-fix issues
poetry run ruff check --fix .

# View specific errors
poetry run ruff check
```

## Performance Tips

### Development

- Use `--reload` only in development (slower startup)
- Mock external API calls in tests
- Use `.env` for configuration (don't hardcode)

### Testing

- Use pytest markers to group tests: `@pytest.mark.slow`
- Run fast tests frequently, slow tests before commits
- Use fixtures to avoid repeated setup

### Debugging

- Use `logging` instead of `print()`
- Set `DEBUG=True` in `.env` for verbose output
- Use profiling tools for performance issues: `cProfile`, `line_profiler`

## Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Poetry Documentation](https://python-poetry.org/docs/)
- [Pydantic Documentation](https://docs.pydantic.dev/)
- [OpenAI API Reference](https://platform.openai.com/docs/api-reference)
- [pytest Documentation](https://docs.pytest.org/)

## Getting Help

- Check existing issues on GitHub
- Review ARCHITECTURE.md for system design
- Read .claude/PROJECT_CONTEXT.md for AI assistant context
- Ask in team chat or create a GitHub issue

## Next Steps

After setup:
1. Read through ARCHITECTURE.md to understand the system
2. Browse the codebase in `backend/app/`
3. Run the tests to ensure everything works
4. Try adding a new company or event
5. Make a small change and see the workflow in action
