# Campaign Planner Backend

AI-powered campaign planner backend built with FastAPI.

## Prerequisites

- Python 3.11 or higher
- Poetry (Python package manager)

## Setup

1. **Navigate to the backend directory**
   ```bash
   cd backend
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```
   This will create a virtual environment in `backend/.venv` and install all required dependencies.

3. **Configure environment variables**
   ```bash
   cp .env.example .env
   ```
   Edit `.env` and add your configuration:
   - `OPENAI_API_KEY` - Your OpenAI API key (required)
   - `FACEBOOK_ACCESS_TOKEN` - For Facebook publishing (optional)
   - `INSTAGRAM_ACCESS_TOKEN` - For Instagram publishing (optional)
   - Other settings as needed

## Running the Application

**Development server with auto-reload:**
```bash
poetry run uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

- API documentation: `http://localhost:8000/docs`
- Health check: `http://localhost:8000/health`

## Development

**Activate the virtual environment:**
```bash
poetry shell
```

**Run tests:**
```bash
poetry run pytest
```

**Code formatting and linting:**
```bash
# Format code with black
poetry run black .

# Lint with ruff
poetry run ruff check .

# Auto-fix ruff issues
poetry run ruff check --fix .
```

**Pre-commit hooks:**

The repository uses pre-commit hooks for code quality. They run automatically on commit, but you can also run them manually:
```bash
pre-commit run --all-files
```

## Project Structure

```
backend/
├── app/
│   ├── common/         # Shared utilities and services
│   ├── core/           # Core configuration and setup
│   ├── features/       # Feature modules (companies, events, generation, publishing)
│   ├── schedulers/     # Background job schedulers
│   └── main.py         # Application entry point
├── data/               # Data storage directory
├── tests/              # Test files
└── pyproject.toml      # Project dependencies and configuration
```

## Key Technologies

- **FastAPI** - Modern web framework
- **Pydantic** - Data validation
- **OpenAI** - AI content generation
- **APScheduler** - Task scheduling
- **Poetry** - Dependency management
