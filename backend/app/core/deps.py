from __future__ import annotations

import time
from collections import defaultdict

from fastapi import Depends, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.db import get_db
from app.core.security import ACCESS_COOKIE, decode_access_token
from app.modules.auth.models import User

# In-memory sliding window. Redis-backed token bucket is the planned
# upgrade (plan/01 §8: Redis token bucket per user/IP on auth endpoints).
_attempts: dict[str, list[float]] = defaultdict(list)
_WINDOW = 60.0


def check_rate_limit(ip: str, limit: int = settings.login_rate_limit_per_minute) -> None:
    now = time.monotonic()
    window = [t for t in _attempts[ip] if now - t < _WINDOW]
    _attempts[ip] = window
    if len(window) >= limit:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Too many attempts. Try again in a minute.",
        )


def record_attempt(ip: str) -> None:
    _attempts[ip].append(time.monotonic())


def get_client_ip(request: Request) -> str:
    return request.client.host if request.client else "unknown"


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> User:
    """Auth guard: raises 401 unless a valid access-token cookie is present."""
    token = request.cookies.get(ACCESS_COOKIE)
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    try:
        payload = decode_access_token(token)
        if payload.get("type") != "access":
            raise ValueError("wrong token type")
    except Exception:  # noqa: BLE001 - any decode failure means "not authenticated"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Session expired or invalid.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    user = await db.get(User, payload["sub"])
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User no longer exists.",
        )
    return user