"""CampaignPulse — AI-Powered Campaign Intelligence Platform.

FastAPI backend providing unified campaign management, AI creative analysis,
budget optimization, landing page tracking, and automated anomaly detection.
"""

from __future__ import annotations

import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.auth import verify_api_key_middleware
from app.config import settings
from app.database import engine
from app.models import Base
from app.seed_data import seed_demo_data

logging.basicConfig(
    level=getattr(logging, settings.log_level.upper(), logging.INFO),
    format="%(asctime)s  %(levelname)-8s %(name)s  %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: create tables and seed demo data on startup."""
    logger.info("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    seed_demo_data()
    logger.info("CampaignPulse backend started successfully")
    yield


app = FastAPI(
    title="CampaignPulse API",
    description="AI-powered campaign intelligence platform for media buyers",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS
origins = [o.strip() for o in settings.cors_origins.split(",") if o.strip()]
if origins and "*" in origins:
    logger.warning(
        "CORS configured with wildcard origin — credentials will be disallowed "
        "by the browser. In production, set CORS_ORIGINS to specific origins."
    )
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- Authentication middleware ---
# Exempt /api/health from API key checks
@app.middleware("http")
async def authenticate_request(request: Request, call_next) -> JSONResponse:
    """Validate API key on all routes except /api/health."""
    if request.url.path == "/api/health":
        return await call_next(request)

    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        token = auth_header.removeprefix("Bearer ")
        try:
            verify_api_key_middleware(token)
        except Exception:
            if settings.api_key:
                logger.warning("Unauthorized request to %s", request.url.path)
                return JSONResponse(
                    status_code=403,
                    content={"detail": "Invalid API key"},
                )
    elif settings.api_key:
        return JSONResponse(
            status_code=401,
            content={"detail": "Missing Authorization header"},
        )

    return await call_next(request)


# --- Security headers middleware ---
# Applies headers AFTER the response is generated (wraps outer middleware)
@app.middleware("http")
async def add_security_headers(request: Request, call_next) -> JSONResponse:
    """Add security headers to every response."""
    response = await call_next(request)
    response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = (
        "camera=(), microphone=(), geolocation=(), interest-cohort=()"
    )
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; "
        "img-src 'self' data:; font-src 'self'; connect-src 'self'"
    )
    return response


# Register routers
from app.routes.budget import router as budget_router  # noqa: E402
from app.routes.campaigns import router as campaigns_router  # noqa: E402
from app.routes.creatives import router as creatives_router  # noqa: E402
from app.routes.insights import router as insights_router  # noqa: E402
from app.routes.landing_pages import router as landing_pages_router  # noqa: E402
from app.routes.mcp import router as mcp_router  # noqa: E402
from app.routes.platforms import router as platforms_router  # noqa: E402

app.include_router(campaigns_router)
app.include_router(creatives_router)
app.include_router(platforms_router)
app.include_router(budget_router)
app.include_router(landing_pages_router)
app.include_router(insights_router)
app.include_router(mcp_router)


@app.get("/api/health")
def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok", "service": "CampaignPulse API"}
