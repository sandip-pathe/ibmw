"""
FastAPI application entry point.
"""
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from loguru import logger
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from app.api import (
    admin, 
    analysis, 
    installations, 
    webhooks, 
    user_repos, 
    auth, 
    regulations,
    violations,
    integrations,
    job_status,
    mcp_server,    # MCP orchestration endpoints
    hitl_review    # HITL reviewer tools
)
from app.config import get_settings
from app.database import db
from app.services.rss_scraper import rss_agent
from app.workers.job_queue import job_queue

load_dotenv()

settings = get_settings()

# Initialize Scheduler
scheduler = AsyncIOScheduler()

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"Starting {settings.app_name} v{settings.api_version}")
    logger.info(f"Environment: {settings.environment}")
    await db.connect()
    await job_queue.connect_async()

    # Start RSS Scheduler only if enabled
    scheduler_started = False
    if getattr(settings, "enable_rss_scraper", False):
        scheduler.add_job(rss_agent.run_scrape_cycle, 'interval', minutes=5)
        scheduler.start()
        scheduler_started = True
        logger.info("RSS Scraper Scheduler started (5 min interval)")

    # Optional: Initialize Sentry
    if settings.sentry_dsn:
        import sentry_sdk
        sentry_sdk.init(
            dsn=settings.sentry_dsn,
            environment=settings.environment,
            traces_sample_rate=0.1 if settings.is_production else 1.0,
        )
        logger.info("Sentry initialized")

    logger.info("Application startup complete")
    yield
    logger.info("Shutting down application")
    await db.disconnect()
    await job_queue.disconnect_async()
    if scheduler_started:
        scheduler.shutdown()
    logger.info("Application shutdown complete")

app = FastAPI(
    title=settings.app_name,
    version=settings.api_version,
    description="AI-powered compliance automation for fintech code repositories",
    lifespan=lifespan,
    docs_url="/docs" if not settings.is_production else None,
    redoc_url="/redoc" if not settings.is_production else None,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"] if settings.is_development else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Exception handlers
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning(f"Validation error: {exc.errors()}")
    return JSONResponse(
        status_code=422,
        content={
            "error": "Validation Error",
            "detail": exc.errors(),
        },
    )

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unexpected error: {exc}", exc_info=True)
    if settings.is_production:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred",
            },
        )
    else:
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Server Error",
                "detail": str(exc),
            },
        )

# Include routers
app.include_router(auth.router)
app.include_router(webhooks.router)
app.include_router(installations.router)
app.include_router(analysis.router)
app.include_router(admin.router)
app.include_router(user_repos.router)
app.include_router(regulations.router)
app.include_router(violations.router)
app.include_router(integrations.router)
app.include_router(job_status.router)
app.include_router(mcp_server.router)    # MCP orchestration endpoints
app.include_router(hitl_review.router)   # HITL reviewer tools

# Root endpoint
@app.get("/")
async def root():
    return {
        "service": settings.app_name,
        "version": settings.api_version,
        "environment": settings.environment,
        "docs": "/docs" if not settings.is_production else "disabled",
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}

# Optional: Prometheus metrics
if getattr(settings, "enable_metrics", False):
    from prometheus_client import make_asgi_app
    metrics_app = make_asgi_app()
    app.mount("/metrics", metrics_app)
    logger.info("Prometheus metrics enabled at /metrics")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=getattr(settings, "is_development", False),
        log_level=getattr(settings, "log_level", "info").lower(),
    )