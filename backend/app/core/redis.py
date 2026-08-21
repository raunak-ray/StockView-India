from __future__ import annotations

import redis.asyncio as redis

from app.core.config import settings

_client: redis.Redis | None = None


def get_redis() -> redis.Redis:
    """Shared async Redis client (connection pool is managed by redis-py)."""
    global _client
    if _client is None:
        _client = redis.from_url(settings.redis_url, decode_responses=True)
    return _client


async def close_redis() -> None:
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None
