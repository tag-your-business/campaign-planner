# V1 Implementation Plan - AI Social Media Automation Platform

## Overview

Campaign Planner V1 is an autonomous AI-powered social media campaign generation and publishing system. It automatically creates and publishes festival/holiday campaigns for multiple companies on Facebook and Instagram.

## Feature Scope

### Platforms
- Facebook (via Graph API v21.0)
- Instagram (via Graph API v21.0)

### Content Types
- Single image posts with captions
- Industry-specific branding
- Event-based campaigns

### AI Models
- **Text Generation**: GPT-4o-mini for captions
- **Image Generation**: DALL-E 3 for social media images
- **Image Processing**: Pillow for logo overlay and branding

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────┐
│                     Campaign Planner V1                      │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌──────────────┐         ┌──────────────┐                  │
│  │   Scheduler  │         │   REST API   │                  │
│  │   (APScheduler)│         │  (FastAPI)   │                  │
│  └──────┬───────┘         └──────┬───────┘                  │
│         │                         │                           │
│         v                         v                           │
│  ┌──────────────────────────────────────┐                   │
│  │      Generation Pipeline             │                   │
│  │  ┌────────────┐  ┌────────────┐     │                   │
│  │  │ Campaign   │  │  Prompt    │     │                   │
│  │  │ Planner    │→ │ Generator  │     │                   │
│  │  └────────────┘  └────────────┘     │                   │
│  │         ↓              ↓              │                   │
│  │  ┌────────────┐  ┌────────────┐     │                   │
│  │  │  Caption   │  │   Image    │     │                   │
│  │  │ Generator  │  │  Service   │     │                   │
│  │  │ (GPT-4o)   │  │ (DALL-E 3) │     │                   │
│  │  └────────────┘  └────────────┘     │                   │
│  │         ↓              ↓              │                   │
│  │  ┌────────────────────────────┐     │                   │
│  │  │   Branding Service         │     │                   │
│  │  │   (Logo Overlay)           │     │                   │
│  │  └────────────────────────────┘     │                   │
│  └──────────────────────────────────────┘                   │
│                    ↓                                          │
│  ┌──────────────────────────────────────┐                   │
│  │      Storage Service                 │                   │
│  │      (JSON Filesystem)               │                   │
│  └──────────────────────────────────────┘                   │
│                    ↓                                          │
│  ┌──────────────────────────────────────┐                   │
│  │      Publishing Pipeline             │                   │
│  │  ┌────────────┐  ┌────────────┐     │                   │
│  │  │ Facebook   │  │ Instagram  │     │                   │
│  │  │ Publisher  │  │ Publisher  │     │                   │
│  │  └────────────┘  └────────────┘     │                   │
│  └──────────────────────────────────────┘                   │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

## Implementation Phases

### Phase 1: AI Content Generation ✅
- ✅ PromptGenerator: Template system for DALL-E prompts
- ✅ CaptionGenerator: GPT-4o-mini integration with retry logic
- ✅ CampaignPlanner: Event-company matching based on industry
- ✅ BrandingService: Logo overlay using Pillow

### Phase 2: Social Media Publishing ✅
- ✅ FacebookPublisher: Graph API v21.0 integration
- ✅ InstagramPublisher: 2-step publishing (container + publish)

### Phase 3: Scheduler & Orchestration ✅
- ✅ run_generate_job(): Full generation pipeline
- ✅ run_publish_job(): Publishing pipeline
- ✅ APScheduler integration with cron triggers

### Phase 4: API Endpoints ✅
- ✅ `/api/v1/campaigns/*`: Generate, publish, list campaigns
- ✅ `/api/v1/companies/*`: List companies, get profiles
- ✅ `/api/v1/events/{year}`: Get events for a year

### Phase 5: Configuration ✅
- ✅ Updated config.py with new parameters
- ✅ Added tenacity and pillow dependencies
- ✅ Updated .env.example with all variables

### Phase 6: Documentation ✅
- ✅ v1_plan.md (this file)
- ⏳ v1_milestone.md

## Success Criteria

### Completed ✅
- [x] All NotImplementedError stubs replaced with working code
- [x] Configuration system updated
- [x] Dependencies added (tenacity, pillow)
- [x] AI content generation pipeline complete
- [x] Social media publishing complete
- [x] Scheduler integration complete
- [x] API endpoints created
- [x] Error handling with retry logic
- [x] Logging throughout the system

### In Progress / To Test
- [ ] System runs autonomously for 7 days
- [ ] Campaigns auto-generated 10 days before events
- [ ] Campaigns auto-published 3 days before events
- [ ] Posts successfully appear on Facebook & Instagram
- [ ] Manual API triggers work correctly
- [ ] No critical bugs or crashes

## Timeline

**Actual Implementation**: ~3-4 hours (compressed from 13 days)

All core features implemented:
- Phase 1 (Generation): Complete
- Phase 2 (Publishing): Complete
- Phase 3 (Scheduling): Complete
- Phase 4 (API): Complete
- Phase 5 (Config): Complete
- Phase 6 (Docs): In Progress

## Known V1 Limitations

1. **Storage**: JSON files (not scalable beyond ~100 companies)
2. **Instagram**: Requires publicly accessible image URLs (note in code)
3. **Error Recovery**: Logged but requires manual intervention
4. **Approval**: No human review workflow
5. **Analytics**: No performance tracking
6. **Platforms**: Only Facebook & Instagram
7. **Content Types**: Only single image posts
8. **Testing**: Manual testing required (no automated tests yet)

## Post-V1 Roadmap

### V2 Features
- PostgreSQL database migration
- Approval workflow UI (admin portal)
- Campaign analytics dashboard
- Additional platforms (LinkedIn, Twitter, Google Business Profile)
- Video generation support
- Custom campaigns (not just events)

### V3+ Features
- Multi-user authentication
- Webhook integrations
- Performance optimization (parallel generation)
- Cloud storage (S3 migration)
- A/B testing
- Automated performance analysis

## Getting Started

### Prerequisites
- Python 3.13+
- OpenAI API key
- Facebook/Instagram access tokens (for publishing)

### Installation

```bash
cd backend
poetry install

# Configure environment
cp .env.example .env
# Edit .env with your API keys
```

### Running Locally

```bash
# Development mode
poetry run uvicorn app.main:app --reload

# Access API docs
open http://localhost:8000/docs
```

### Manual Testing

```bash
# Trigger generation
curl -X POST http://localhost:8000/api/v1/campaigns/generate

# List pending campaigns
curl http://localhost:8000/api/v1/campaigns/pending

# Trigger publishing
curl -X POST http://localhost:8000/api/v1/campaigns/publish
```

## Configuration

### Environment Variables

See `.env.example` for all available configuration options:

- **Required**: `OPENAI_API_KEY`
- **Optional**: Timing, scheduling, social media tokens
- **Defaults**: Sensible defaults for development

### Scheduling

Default cron schedules:
- Generation: `0 8 * * *` (daily at 8 AM)
- Publishing: `0 10 * * *` (daily at 10 AM)

Customize via `GENERATE_CRON` and `PUBLISH_CRON` environment variables.

## Support

For issues or questions:
1. Check logs in `data/logs/`
2. Review campaign metadata in `data/campaigns/generated/`
3. Verify configuration in `.env`
4. Check API docs at `/docs` endpoint

## License

Internal project - not licensed for external use.
