"""
middleware/rate_limiter.py — HostelOps AI
==========================================
Redis-based rate limiter for API endpoints.
Uses sliding window counter pattern.
Fails open — if Redis is unavailable, requests are allowed through.
"""
import logging
from typing import Optional

import redis.asyncio as aioredis
from fastapi import HTTPException

from config import settings

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Shared Redis connection
# ---------------------------------------------------------------------------

_redis_client: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    """
    Lazy-initialise and return a shared async Redis client.
    Uses the same Redis URL as Celery (Upstash).
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(
            settings.CELERY_BROKER_URL,
            decode_responses=True,
            ssl_cert_reqs=None,  # Upstash uses TLS; skip cert verification
        )
    return _redis_client


# ---------------------------------------------------------------------------
# RateLimiter class
# ---------------------------------------------------------------------------


class RateLimiter:
    def __init__(self, redis_client: aioredis.Redis):
        self.redis = redis_client

    async def check_rate_limit(
        self,
        action: str,
        user_id: str,
        max_requests: int,
        window_seconds: int,
        rate_limit_message: Optional[str] = None,
    ) -> None:
        """
        Raises HTTP 429 if limit exceeded.
        Returns None if under limit.
        Fails open on Redis errors — logs warning and allows request.
        """
        key = f"ratelimit:{action}:{user_id}:{window_seconds}"
        try:
            current = await self.redis.incr(key)
            if current == 1:
                await self.redis.expire(key, window_seconds)
            if current > max_requests:
                ttl = await self.redis.ttl(key)
                remaining = max(0, max_requests - current)
                if action == "complaint":
                    detail_msg = f"Rate limit exceeded. You can file {remaining} more complaints today."
                else:
                    detail_msg = rate_limit_message or f"Rate limit exceeded. Try again in {ttl} seconds."
                raise HTTPException(
                    status_code=429,
                    detail=detail_msg,
                )
        except HTTPException:
            raise  # Re-raise 429 — don't swallow it
        except Exception as e:
            logger.warning(f"Redis unavailable for rate limiting: {e}")
            # Fail open: allow request through
            return

    async def check_general_rate_limit(self, user_id: str) -> None:
        """General API rate limit: 100 requests per user per minute."""
        await self.check_rate_limit(
            "general_api", user_id, 100, 60,
            "Too many requests. Please slow down.",
        )


# ---------------------------------------------------------------------------
# FastAPI dependency
# ---------------------------------------------------------------------------


async def get_rate_limiter() -> RateLimiter:
    """FastAPI dependency. Returns a RateLimiter backed by the shared Redis client."""
    redis_client = await get_redis()
    return RateLimiter(redis_client)
