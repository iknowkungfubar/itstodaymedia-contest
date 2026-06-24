"""API key authentication for CampaignPulse.

Provides both:
- verify_api_key_middleware(token: str) — called directly from middleware
- VerifyApiKey dependency class — for per-route Depends injection if needed
"""

from __future__ import annotations

import logging
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

logger = logging.getLogger(__name__)


def verify_api_key_middleware(token: str) -> None:
    """Verify an API key token string.

    Called from middleware for all routes except /api/health.
    If no API key is configured, authentication is disabled (dev mode).
    """
    if not settings.api_key:
        return  # No key configured → auth disabled (dev mode)

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing API key",
        )

    if token != settings.api_key:
        logger.warning("Failed API key authentication attempt")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )


_security = HTTPBearer(auto_error=False)


def verify_api_key(
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(_security)],
) -> None:
    """FastAPI Depends-based API key verification.

    Use this as a route dependency for per-route protection.
    If no API key is configured, authentication is disabled (dev mode).
    """
    if not settings.api_key:
        return

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization scheme — use Bearer",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if credentials.credentials != settings.api_key:
        logger.warning("Failed API key authentication attempt")
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API key",
        )
