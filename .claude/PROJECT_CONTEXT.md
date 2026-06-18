# Campaign Planner - Project Context

This document provides comprehensive context for AI assistants (Claude Code, Cursor, etc.) working on this codebase.

## Project Overview

**Campaign Planner** is an AI-powered social media campaign automation system that generates and publishes branded content for businesses. The system uses OpenAI's GPT and gpt-image-2 models to create campaign plans, generate captions, and create images tailored to specific events and business profiles.

### Key Capabilities

- Automated campaign generation based on calendar events (holidays, awareness days, etc.)
- AI-generated social media captions with brand-appropriate tone and messaging
- AI-generated images using gpt-image-2 that match brand colors and style
- Scheduled publishing to Facebook and Instagram
- Multi-company support with individual brand profiles

## Technology Stack

### Backend
- **FastAPI**: Modern async web framework for the API
- **Python 3.13+**: Primary language
- **Poetry**: Dependency management and packaging
- **Pydantic**: Data validation and settings management
- **OpenAI SDK**: For GPT (text) and gpt-image-2 (images) generation
- **APScheduler**: Background task scheduling for automated generation and publishing

### Code Quality Tools
- **Ruff**: Fast Python linter
- **Black**: Code formatter
- **pre-commit**: Git hooks for automated checks
- **pytest**: Testing framework

## Project Structure

```
campaign-planner/
├── .claude/                    # AI assistant context and documentation
├── .github/workflows/          # GitHub Actions CI/CD
├── backend/                    # Main application code
│   ├── app/
│   │   ├── api/               # API endpoints (currently minimal)
│   │   │   └── v1/routes/     # Version 1 API routes
│   │   ├── common/            # Shared utilities
│   │   │   ├── models/        # Pydantic models
│   │   │   └── storage/       # File storage service
│   │   ├── core/              # Core configuration
│   │   │   ├── config.py      # Settings and environment variables
│   │   │   └── logging.py     # Logging configuration
│   │   ├── features/          # Feature modules (domain logic)
│   │   │   ├── companies/     # Company profile management
│   │   │   ├── events/        # Event/holiday calendar
│   │   │   ├── generation/    # Content generation (AI)
│   │   │   │   ├── branding.py    # Brand context generation
│   │   │   │   ├── caption.py     # Caption generation
│   │   │   │   ├── content.py     # Content orchestration
│   │   │   │   ├── image.py       # gpt-image-2 image generation
│   │   │   │   ├── planner.py     # Campaign planning
│   │   │   │   └── prompt.py      # Prompt engineering
│   │   │   └── publishing/    # Social media publishing
│   │   │       └── publishers/    # Platform-specific publishers
│   │   │           ├── facebook.py
│   │   │           └── instagram.py
│   │   ├── schedulers/        # Background job schedulers
│   │   │   ├── generate_scheduler.py  # Campaign generation scheduler
│   │   │   └── publish_scheduler.py   # Publishing scheduler
│   │   └── main.py            # FastAPI application entry point
│   ├── data/                  # Data storage (JSON-based)
│   │   ├── companies/         # Company profiles (one folder per company)
│   │   │   └── {company_slug}/
│   │   │       └── profile.json   # Company details, branding, social IDs
│   │   ├── events/            # Event calendars by year
│   │   │   └── 2026.json      # Events for 2026
│   │   ├── campaigns/         # Generated campaigns (created at runtime)
│   │   ├── registry/          # Company registry
│   │   │   └── company_registry.json
│   │   └── logs/              # Application logs
│   ├── tests/                 # Test files
│   │   ├── unit/              # Unit tests
│   │   └── integration/       # Integration tests
│   └── pyproject.toml         # Poetry dependencies and tool config
├── frontend/                   # Frontend (placeholder)
└── README.md                   # Main project README
```

## Core Workflows

### 1. Campaign Generation Flow
1. **Scheduler triggers** (daily at 8 AM by default via `generate_scheduler.py`)
2. **Event lookup**: Find relevant events from calendar for target dates
3. **Company iteration**: For each registered company:
   - Load company profile (branding, tone, industry)
   - Generate campaign plan using GPT
   - Generate caption with brand voice
   - Generate image with gpt-image-2 (brand colors applied)
   - Save campaign to `data/campaigns/{company_slug}/{campaign_id}/`

### 2. Publishing Flow
1. **Scheduler triggers** (daily at 10 AM by default via `publish_scheduler.py`)
2. **Campaign lookup**: Find scheduled campaigns ready to publish
3. **Platform publishing**: Post to Facebook and/or Instagram
4. **Status tracking**: Mark campaigns as published

## Key Components

### Company Profiles (`backend/app/features/companies/`)
- **Location**: `data/companies/{company_slug}/profile.json`
- **Contains**: Company name, industry, tone, brand colors, social media IDs
- **Example**: ABC Dental with professional tone and dental industry context

### Events Calendar (`backend/app/features/events/`)
- **Location**: `data/events/{year}.json`
- **Contains**: List of holidays, awareness days, and special events
- **Used for**: Identifying relevant dates for campaign generation

### Generation Module (`backend/app/features/generation/`)
- **branding.py**: Generates brand context strings from company profiles
- **caption.py**: Uses GPT to generate brand-appropriate captions
- **content.py**: Orchestrates the full content generation pipeline
- **image.py**: Uses gpt-image-2 to generate branded images
- **planner.py**: Creates campaign plans matching events to companies
- **prompt.py**: Manages prompt templates for AI generation

### Publishing (`backend/app/features/publishing/`)
- **facebook.py**: Facebook Graph API integration
- **instagram.py**: Instagram Graph API integration
- **service.py**: Publishing orchestration

### Storage (`backend/app/common/storage/`)
- JSON-based file storage system
- Handles reading/writing company profiles, events, campaigns
- No database currently (all data in JSON files)

## Environment Variables

Key environment variables (see `backend/.env.example`):

```bash
# Required
OPENAI_API_KEY=sk-...              # OpenAI API key for GPT and gpt-image-2

# Optional (for publishing)
FACEBOOK_ACCESS_TOKEN=...           # Facebook Graph API token
INSTAGRAM_ACCESS_TOKEN=...          # Instagram Graph API token

# Scheduler timing (cron format)
GENERATE_CRON="0 8 * * *"          # When to generate campaigns
PUBLISH_CRON="0 10 * * *"          # When to publish campaigns

# Paths (usually defaults are fine)
DATA_DIR=data
REGISTRY_PATH=data/registry/company_registry.json
COMPANIES_DIR=data/companies
EVENTS_DIR=data/events
CAMPAIGNS_DIR=data/campaigns
```

## Development Guidelines

### Code Style
- Use **Black** for formatting (line length: 100)
- Use **Ruff** for linting
- Type hints encouraged but not enforced
- Async/await for I/O operations

### Testing
- Unit tests in `tests/unit/`
- Integration tests in `tests/integration/`
- Use pytest for all tests
- Async tests supported via pytest-asyncio

### Feature Organization
- Features are organized by domain (companies, events, generation, publishing)
- Each feature has its own service module
- Keep domain logic separate from API routes

## Common Tasks for AI Assistants

### Adding a New Company
1. Create folder: `backend/data/companies/{company_slug}/`
2. Create `profile.json` with company details
3. Add entry to `backend/data/registry/company_registry.json`

### Adding a New Event
1. Edit `backend/data/events/{year}.json`
2. Add event with name, date, description

### Modifying Generation Logic
- Caption generation: `backend/app/features/generation/caption.py`
- Image generation: `backend/app/features/generation/image.py`
- Prompt templates: `backend/app/features/generation/prompt.py`

### Adding a New Social Platform
1. Create publisher: `backend/app/features/publishing/publishers/{platform}.py`
2. Implement publishing interface
3. Add credentials to `.env` and `config.py`

## Important TODOs in Codebase

From `backend/app/main.py`:
- Line 12: Start schedulers in lifespan startup
- Line 14: Shutdown schedulers in lifespan cleanup

These indicate the scheduler integration is planned but not yet implemented in the FastAPI lifecycle.

## Data Schema Examples

### Company Profile (`profile.json`)
```json
{
  "slug": "abc_dental",
  "name": "ABC Dental",
  "industry": "dental",
  "tone": "professional",
  "brand_colors": ["#0057B7", "#FFFFFF"],
  "social": {
    "facebook_page_id": "",
    "instagram_account_id": ""
  }
}
```

### Event Entry
```json
{
  "date": "2026-02-14",
  "name": "Valentine's Day",
  "description": "Day of romance and love",
  "tags": ["holiday", "romantic"]
}
```

## Key Design Decisions

1. **JSON Storage**: Using file-based JSON storage instead of a database for simplicity and ease of version control
2. **OpenAI Integration**: Leveraging GPT for text and gpt-image-2 for images to ensure consistent quality
3. **Scheduler-based**: Automated generation and publishing via cron-like schedulers
4. **Multi-tenant by Company**: Each company has isolated profile and campaigns
5. **Feature-based Architecture**: Domain logic organized by business capability, not technical layer

## File Naming Conventions

- Snake case for Python files: `generate_scheduler.py`
- Lowercase for directories: `features/`, `publishers/`
- Company slugs in data directories: `abc_dental/`
- Campaign IDs use timestamps or UUIDs (TBD based on implementation)

## When Making Changes

1. **Always read relevant files first** before making changes
2. **Understand the feature module** you're working in
3. **Check environment variables** in `config.py` if adding new settings
4. **Update tests** when modifying core logic
5. **Run pre-commit hooks** before committing: `poetry run pre-commit run --all-files`
6. **Maintain backward compatibility** with existing data schemas
7. **Document new features** in appropriate README or architecture docs

## Getting Started as an AI Assistant

When tasked with modifying this codebase:
1. Read this file first for context
2. Read the specific feature module you'll be working on
3. Check `backend/app/core/config.py` for available settings
4. Review test files to understand expected behavior
5. Make changes incrementally and test
6. Use the existing code style and patterns

## Questions to Ask the User

Before implementing features, consider asking:
- "Which company profile should this apply to?"
- "Should this be configurable via environment variables?"
- "Do you want this to affect all existing campaigns or only new ones?"
- "Should we add tests for this feature?"
- "Do you need this deployed immediately or can it wait for the next release?"