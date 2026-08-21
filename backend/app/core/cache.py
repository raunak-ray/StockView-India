from __future__ import annotations

import json
import logging
from typing import Any

from redis.exceptions import RedisError

from app.core.redis import get_redis

logger = logging.getLogger(__name__)

# Cache failures must never take an endpoint down: on any Redis error we log
# at warning level and fall through to a direct upstream fetch.


async def cache_get(key: str) -> Any | None:
    try:
        raw = await get_redis().get(key)
    except RedisError as exc:
        logger.warning("cache_get failed for %s: %s", key, exc)
        return None
    if raw is None:
        return None
    return json.loads(raw)


async def cache_set(key: str, value: Any, ttl_seconds: int) -> None:
    try:
        await get_redis().set(key, json.dumps(value), ex=ttl_seconds)
    except RedisError as exc:
        logger.warning("cache_set failed for %s: %s", key, exc)
