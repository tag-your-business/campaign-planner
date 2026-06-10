import logging
from contextlib import asynccontextmanager

from app.api.v1.routes import campaigns, companies, events
from app.core.config import settings
from app.core.logging import setup_logging
from app.schedulers.generate_scheduler import run_generate_job
from app.schedulers.publish_scheduler import run_publish_job
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from fastapi import FastAPI

logger = logging.getLogger(__name__)

scheduler = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager - handles startup and shutdown."""
    global scheduler

    # Startup
    setup_logging()
    logger.info("Starting Campaign Planner application")

    # Initialize and start scheduler
    scheduler = AsyncIOScheduler()

    # Add generation job
    scheduler.add_job(
        run_generate_job,
        CronTrigger.from_crontab(settings.generate_cron),
        id="generate_campaigns",
        name="Generate Campaigns",
        replace_existing=True,
    )
    logger.info(f"Scheduled generate job with cron: {settings.generate_cron}")

    # Add publish job
    scheduler.add_job(
        run_publish_job,
        CronTrigger.from_crontab(settings.publish_cron),
        id="publish_campaigns",
        name="Publish Campaigns",
        replace_existing=True,
    )
    logger.info(f"Scheduled publish job with cron: {settings.publish_cron}")

    # Start scheduler
    scheduler.start()
    logger.info("Schedulers started successfully")

    yield

    # Shutdown
    if scheduler:
        scheduler.shutdown(wait=True)
        logger.info("Schedulers shut down")


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

# Register API routers
app.include_router(campaigns.router, prefix="/api/v1")
app.include_router(companies.router, prefix="/api/v1")
app.include_router(events.router, prefix="/api/v1")


@app.get("/health")
def health():
    """Health check endpoint."""
    return {"status": "ok"}
