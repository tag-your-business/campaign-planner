# Campaign Planner - Architecture Documentation

## System Overview

Campaign Planner is an AI-powered social media automation system built with a feature-based architecture. The system follows a scheduled workflow where campaigns are generated in advance and published at specified times.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Application                      │
│                          (app/main.py)                           │
└────────────────────┬────────────────────────────────────────────┘
                     │
        ┌────────────┴────────────┐
        │                         │
┌───────▼────────┐       ┌───────▼────────┐
│  API Layer     │       │   Schedulers   │
│  (api/v1/)     │       │ (schedulers/)  │
└────────────────┘       └───────┬────────┘
                                 │
                    ┌────────────┼────────────┐
                    │                         │
          ┌─────────▼────────┐    ┌──────────▼────────┐
          │ Generate Scheduler│    │ Publish Scheduler │
          │  (Daily 8 AM)     │    │  (Daily 10 AM)    │
          └─────────┬─────────┘    └──────────┬────────┘
                    │                         │
                    └────────────┬────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │     Feature Modules      │
                    │      (features/)         │
                    └────────────┬─────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
┌───────▼────────┐    ┌──────────▼────────┐   ┌─────────▼─────────┐
│   Companies    │    │    Generation     │   │   Publishing      │
│   (profiles)   │    │  (AI content)     │   │  (social media)   │
└───────┬────────┘    └──────────┬────────┘   └─────────┬─────────┘
        │                        │                       │
        │             ┌──────────┼──────────┐           │
        │             │          │          │           │
        │      ┌──────▼─────┐ ┌──▼────┐ ┌──▼──────┐    │
        │      │  Caption   │ │ Image │ │ Planner │    │
        │      │  (GPT)     │ │(gpt-image-2)│ │  (GPT)  │    │
        │      └────────────┘ └───────┘ └─────────┘    │
        │                                               │
        ├───────────────────────────────────────────────┤
        │                                               │
┌───────▼───────────────────────────────────────────────▼────────┐
│                      Storage Layer                              │
│                   (common/storage/)                             │
│                                                                 │
│  ┌─────────────┐  ┌─────────────┐  ┌──────────┐  ┌─────────┐ │
│  │  Companies  │  │   Events    │  │ Campaigns│  │  Logs   │ │
│  │   (JSON)    │  │   (JSON)    │  │  (JSON)  │  │ (files) │ │
│  └─────────────┘  └─────────────┘  └──────────┘  └─────────┘ │
└─────────────────────────────────────────────────────────────────┘
                                 │
                    ┌────────────▼─────────────┐
                    │   External Services      │
                    ├──────────────────────────┤
                    │  • OpenAI API (GPT)      │
                    │  • gpt-image-2 API            │
                    │  • Facebook Graph API    │
                    │  • Instagram Graph API   │
                    └──────────────────────────┘
```

## Core Components

### 1. Application Core (`app/core/`)

#### Configuration (`config.py`)
- Centralized settings management using Pydantic Settings
- Environment variable loading from `.env`
- Type-safe configuration access
- Default values for all settings

**Key Responsibilities:**
- API keys management (OpenAI, Facebook, Instagram)
- Path configuration for data directories
- Scheduler timing (cron expressions)
- Application-level settings (debug mode, app name)

#### Logging (`logging.py`)
- Structured logging setup
- Log file rotation
- Console and file output
- Debug/production modes

### 2. Feature Modules (`app/features/`)

The system uses a feature-based architecture where each business capability is encapsulated in its own module.

#### Companies Feature (`features/companies/`)
**Purpose**: Manage company profiles and branding information

**Components:**
- `service.py`: Company CRUD operations, profile loading

**Data Structure:**
```
data/companies/{company_slug}/
    profile.json          # Company metadata and branding
```

**Responsibilities:**
- Load company profiles from storage
- Provide company metadata to generation pipeline
- Validate company configurations

#### Events Feature (`features/events/`)
**Purpose**: Manage calendar events (holidays, awareness days)

**Components:**
- `service.py`: Event loading, filtering, date-based queries

**Data Structure:**
```
data/events/
    2026.json            # Events for 2026
    2027.json            # Events for 2027 (future)
```

**Responsibilities:**
- Load event calendars by year
- Filter events by date range
- Match events to company industries/themes

#### Generation Feature (`features/generation/`)
**Purpose**: AI-powered content generation for campaigns

**Components:**
- `branding.py`: Brand context string generation
- `caption.py`: GPT-based caption generation
- `content.py`: Content pipeline orchestration
- `image.py`: gpt-image-2 image generation
- `planner.py`: Campaign planning logic
- `prompt.py`: Prompt engineering and templates

**Data Flow:**
```
Event + Company → Planner → Caption Generator → Image Generator → Campaign
                     ↓            ↓                   ↓
                  GPT-5.4       GPT-5.4              gpt-image-2
```

**Responsibilities:**
- Generate brand-appropriate captions
- Create custom images with brand colors
- Plan campaigns matching events to companies
- Maintain prompt templates for AI models

#### Publishing Feature (`features/publishing/`)
**Purpose**: Publish content to social media platforms

**Components:**
- `service.py`: Publishing orchestration
- `publishers/facebook.py`: Facebook Graph API integration
- `publishers/instagram.py`: Instagram Graph API integration

**Responsibilities:**
- Post content to social platforms
- Handle platform-specific requirements
- Track publishing status
- Error handling and retries

### 3. Schedulers (`app/schedulers/`)

#### Generate Scheduler (`generate_scheduler.py`)
**Trigger**: Daily at 8 AM (configurable via `GENERATE_CRON`)

**Workflow:**
1. Query events for next N days
2. For each company in registry:
   - Load company profile
   - Match events to company
   - Generate campaign content
   - Save to `data/campaigns/{company}/{campaign_id}/`

#### Publish Scheduler (`publish_scheduler.py`)
**Trigger**: Daily at 10 AM (configurable via `PUBLISH_CRON`)

**Workflow:**
1. Query campaigns scheduled for today
2. For each campaign:
   - Load campaign data
   - Publish to configured platforms
   - Update campaign status
   - Log results

### 4. Common Utilities (`app/common/`)

#### Models (`common/models/`)
- Pydantic models for data validation
- Shared DTOs between features
- Type safety for data structures

#### Storage (`common/storage/`)
**Purpose**: Abstract data persistence layer

**Components:**
- `service.py`: JSON file I/O operations

**Responsibilities:**
- Read/write JSON files
- Directory management
- Data serialization/deserialization
- File path resolution

## Data Architecture

### Storage Strategy

The system uses a file-based JSON storage approach for simplicity and version control friendliness.

```
data/
├── companies/               # Company profiles
│   └── {company_slug}/
│       └── profile.json
├── events/                  # Event calendars
│   └── {year}.json
├── campaigns/               # Generated campaigns
│   └── {company_slug}/
│       └── {campaign_id}/
│           ├── metadata.json
│           ├── caption.txt
│           └── image.png
├── registry/                # Central registries
│   └── company_registry.json
└── logs/                    # Application logs
    └── {date}.log
```

### Data Models

#### Company Profile
```json
{
  "slug": "string",
  "name": "string",
  "industry": "string",
  "tone": "professional | casual | friendly | authoritative",
  "brand_colors": ["#HEX", "#HEX"],
  "social": {
    "facebook_page_id": "string",
    "instagram_account_id": "string"
  }
}
```

#### Event
```json
{
  "date": "YYYY-MM-DD",
  "name": "string",
  "description": "string",
  "tags": ["string"]
}
```

#### Campaign (generated)
```json
{
  "id": "string",
  "company_slug": "string",
  "event_id": "string",
  "scheduled_date": "YYYY-MM-DD",
  "status": "draft | scheduled | published | failed",
  "caption": "string",
  "image_url": "string",
  "platforms": ["facebook", "instagram"],
  "created_at": "ISO8601",
  "published_at": "ISO8601 | null"
}
```

## API Layer (`app/api/`)

Currently minimal. Structure prepared for future expansion:

```
api/
└── v1/
    └── routes/
        # Future endpoints:
        # - GET /companies
        # - POST /campaigns/generate
        # - GET /campaigns/{id}
        # - POST /campaigns/{id}/publish
```

## External Dependencies

### OpenAI
- **GPT Models**: Text generation (captions, plans)
- **gpt-image-2**: Image generation
- **Rate Limits**: Managed via OpenAI SDK

### Social Media APIs
- **Facebook Graph API**: Page posting
- **Instagram Graph API**: Account posting
- **Authentication**: Long-lived access tokens

## Design Patterns

### 1. Service Layer Pattern
Each feature has a service module that encapsulates business logic:
- `CompanyService`
- `EventService`
- `ContentGenerationService`
- `PublishingService`

### 2. Dependency Injection
- Settings injected via `app.core.config.settings`
- Services instantiated at module level or as needed

### 3. Async/Await
- All I/O operations use async/await
- FastAPI endpoints are async
- HTTP clients use httpx for async requests

### 4. Configuration Over Code
- Behavior driven by environment variables
- Scheduler timing configurable
- Platform credentials external
- Paths configurable

## Security Considerations

### API Keys
- Stored in `.env` (not committed)
- Loaded via `pydantic-settings`
- Never logged or exposed

### Data Privacy
- Company data stored locally (JSON files)
- No external database (privacy by design)
- Logs exclude sensitive information

### Access Control
- Social media tokens scoped to specific pages/accounts
- No user authentication yet (single-tenant for now)

## Scalability Considerations

### Current Limitations
- JSON file storage not suitable for high volume
- Single-process scheduler execution
- No distributed task queue
- Synchronous generation pipeline

### Future Enhancements
- Database migration (PostgreSQL recommended)
- Distributed task queue (Celery, RQ, or Temporal)
- Async generation pipeline
- Caching layer (Redis)
- Multi-instance deployment

## Error Handling

### Strategy
- Exceptions bubble up to service layer
- Schedulers catch and log errors
- Failed campaigns marked with status
- Retries not yet implemented

### Logging
- All errors logged with context
- Scheduler execution logged
- AI API calls logged (without sensitive data)

## Testing Strategy

### Unit Tests (`tests/unit/`)
- Test individual services
- Mock external APIs (OpenAI, Facebook, Instagram)
- Test data transformations

### Integration Tests (`tests/integration/`)
- Test feature workflows end-to-end
- Test with real JSON files (test fixtures)
- Test scheduler execution

## Future Architecture Considerations

### Planned Enhancements
1. **API Expansion**: RESTful API for manual campaign management
2. **Web UI**: Frontend for campaign review and approval
3. **Multi-user**: Authentication and multi-tenant support
4. **Analytics**: Campaign performance tracking
5. **A/B Testing**: Multiple caption/image variants
6. **Approval Workflow**: Review before publish
7. **Template System**: Reusable content templates

### Migration Path to Database
When volume increases:
1. Introduce PostgreSQL for relational data
2. Keep JSON for configuration (companies, events)
3. Use database for campaigns, logs, analytics
4. Implement proper migrations (Alembic)

## Development Workflow

1. **Local Development**:
   - Poetry for dependencies
   - uvicorn with auto-reload
   - Manual scheduler trigger for testing

2. **Testing**:
   - pytest for all tests
   - pre-commit hooks for quality

3. **Deployment** (future):
   - Containerization (Docker)
   - Scheduler as background process
   - Health checks via `/health` endpoint

## Monitoring and Observability

### Current State
- File-based logging
- Console output during development

### Future Needs
- Structured logging (JSON format)
- Centralized log aggregation
- Application metrics (Prometheus)
- Error tracking (Sentry)
- Campaign analytics dashboard

## Key Architectural Decisions

| Decision | Rationale | Trade-offs |
|----------|-----------|------------|
| JSON storage | Simplicity, version control friendly | Not scalable, no ACID guarantees |
| Feature-based structure | Domain-driven, clear boundaries | Can lead to some code duplication |
| Scheduler-based | Simple automation, no real-time needs | Fixed timing, no on-demand generation |
| OpenAI integration | High-quality AI content | Cost, rate limits, external dependency |
| FastAPI | Modern, async, auto-docs | Python-only ecosystem |
| Poetry | Modern dependency management | Learning curve for some developers |

## Summary

Campaign Planner uses a straightforward feature-based architecture designed for maintainability and clarity. The system prioritizes:
- **Simplicity**: JSON storage, scheduled workflows
- **Modularity**: Feature-based organization
- **AI-first**: Leveraging OpenAI for quality content
- **Automation**: Hands-off campaign generation and publishing

The architecture is designed to evolve: starting simple with file storage and scheduled jobs, with a clear path to scale with databases, APIs, and distributed processing as needs grow.
