# Campaign Planner

> AI-powered social media campaign automation for businesses

Campaign Planner is an intelligent system that automatically generates and publishes branded social media content. It uses OpenAI's GPT and DALL-E models to create custom campaigns for holidays, awareness days, and special events tailored to each business's unique brand identity.

## Features

- **AI-Powered Content Generation**: Leverages GPT for captions and DALL-E for images
- **Automated Scheduling**: Daily campaign generation and publishing via cron-like schedulers
- **Multi-Company Support**: Manage campaigns for multiple businesses with individual branding
- **Brand-Aware**: Generates content matching company tone, industry, and brand colors
- **Social Media Integration**: Publishes to Facebook and Instagram
- **Event-Driven**: Automatically plans campaigns around holidays and special events

## Quick Start

### Prerequisites

- Python 3.13 or higher
- Poetry (Python package manager)
- OpenAI API key

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd campaign-planner/backend
   ```

2. **Install dependencies**
   ```bash
   poetry install
   ```

3. **Configure environment**
   ```bash
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   ```

4. **Run the application**
   ```bash
   poetry run uvicorn app.main:app --reload
   ```

5. **Access the API**
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs
   - Health: http://localhost:8000/health

## Documentation

- **[Development Guide](DEVELOPMENT.md)** - Setup, workflow, and coding standards
- **[Architecture](ARCHITECTURE.md)** - System design and component details
- **[Contributing](CONTRIBUTING.md)** - How to contribute to the project
- **[AI Context](.claude/PROJECT_CONTEXT.md)** - Context for AI assistants (Claude, Cursor, etc.)

## Project Structure

```
campaign-planner/
├── .claude/              # AI assistant documentation
├── backend/              # FastAPI application
│   ├── app/
│   │   ├── api/         # API routes (future)
│   │   ├── common/      # Shared utilities
│   │   ├── core/        # Configuration and setup
│   │   ├── features/    # Business features
│   │   │   ├── companies/
│   │   │   ├── events/
│   │   │   ├── generation/
│   │   │   └── publishing/
│   │   ├── schedulers/  # Background jobs
│   │   └── main.py      # Application entry
│   ├── data/            # JSON storage
│   ├── tests/           # Test suite
│   └── pyproject.toml   # Dependencies
└── frontend/            # Frontend (future)
```

## Technology Stack

- **[FastAPI](https://fastapi.tiangolo.com/)** - Modern Python web framework
- **[OpenAI](https://platform.openai.com/)** - GPT and DALL-E for content generation
- **[Pydantic](https://docs.pydantic.dev/)** - Data validation
- **[APScheduler](https://apscheduler.readthedocs.io/)** - Task scheduling
- **[Poetry](https://python-poetry.org/)** - Dependency management

## How It Works

1. **Scheduler triggers** daily campaign generation
2. **Event matching** identifies relevant holidays/events
3. **AI generation** creates captions and images for each company
4. **Campaign storage** saves content to JSON files
5. **Publishing scheduler** posts campaigns to social media platforms

See [ARCHITECTURE.md](ARCHITECTURE.md) for detailed workflows and component interactions.

## Development

### Setup Development Environment

```bash
cd backend
poetry install --with dev
poetry run pre-commit install
```

### Run Tests

```bash
poetry run pytest
```

### Code Quality

This repository uses `pre-commit` hooks for code quality:

- `check-ast` - Validate Python syntax
- `check-case-conflict` - Prevent case conflicts
- `check-yaml` / `check-json` / `check-toml` - Validate config files
- `detect-aws-credentials` / `detect-private-key` - Security checks
- `trim-trailing-whitespace` - Clean whitespace
- `autoflake` - Remove unused imports
- `isort` - Sort imports
- `ruff` - Fast Python linter
- `black` - Code formatter

**Run manually:**
```bash
poetry run pre-commit run --all-files
```

See [DEVELOPMENT.md](DEVELOPMENT.md) for complete development workflow.

## Configuration

Key environment variables (in `backend/.env`):

```bash
# Required
OPENAI_API_KEY=sk-...

# Optional (for publishing)
FACEBOOK_ACCESS_TOKEN=...
INSTAGRAM_ACCESS_TOKEN=...

# Scheduler timing (cron format)
GENERATE_CRON="0 8 * * *"   # Daily at 8 AM
PUBLISH_CRON="0 10 * * *"   # Daily at 10 AM
```

## Usage Examples

### Adding a Company

1. Create company profile in `backend/data/companies/company_slug/profile.json`:
   ```json
   {
     "slug": "company_slug",
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

2. Register in `backend/data/registry/company_registry.json`

### Adding Events

Edit `backend/data/events/2026.json`:
```json
{
  "date": "2026-03-15",
  "name": "Event Name",
  "description": "Event description",
  "tags": ["holiday"]
}
```

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

Quick overview:
1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Run pre-commit checks
5. Submit a pull request

## License

See [LICENSE](LICENSE) for details.

## Authors

- Abhay (abhay.30121997@gmail.com)
- Gautam (gautamr347@gmail.com)

## Support

- **Issues**: Report bugs or request features on GitHub Issues
- **Documentation**: Check the docs in this repository
- **AI Assistant Help**: See `.claude/PROJECT_CONTEXT.md` for AI assistant guidance

## Roadmap

- [ ] Complete scheduler integration
- [ ] Build RESTful API endpoints
- [ ] Add web UI for campaign management
- [ ] Implement campaign approval workflow
- [ ] Add analytics and performance tracking
- [ ] Support additional social media platforms (Twitter, LinkedIn)
- [ ] Database migration (PostgreSQL)
- [ ] Multi-user authentication

## Acknowledgments

Built with:
- OpenAI for AI content generation
- FastAPI community for excellent framework and docs
- Python Poetry for modern dependency management
