"""Shared rate limiter used across all endpoints.

Import ``limiter`` from this module and decorate endpoints with
``@limiter.limit("N/minutes")``.

Usage::

    from app.rate_limit import limiter

    @router.post("/scan")
    @limiter.limit("10/minute")
    def scan_for_anomalies(db: DbSession, request: Request):
        ...
"""

from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
