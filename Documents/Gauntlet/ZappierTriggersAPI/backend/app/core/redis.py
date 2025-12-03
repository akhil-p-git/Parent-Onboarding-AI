"""
Redis Configuration and Connection Management.

Provides async Redis client for caching and rate limiting.
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

import redis.asyncio as redis
from redis.asyncio import Redis

from app.core.config import settings

# Global Redis client
_redis_client: Redis | None = None


async def get_redis() -> Redis:
    """
    Get the Redis client instance.

    Returns:
        Redis: Async Redis client
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True,
        )
    return _redis_client


@asynccontextmanager
async def get_redis_context() -> AsyncGenerator[Redis, None]:
    """
    Context manager for Redis connections.

    Usage:
        async with get_redis_context() as redis:
            await redis.set("key", "value")
    """
    client = await get_redis()
    try:
        yield client
    finally:
        pass  # Connection pooling handles cleanup


async def init_redis() -> None:
    """Initialize Redis connection and verify connectivity."""
    client = await get_redis()
    await client.ping()


async def close_redis() -> None:
    """Close Redis connection."""
    global _redis_client
    if _redis_client is not None:
        await _redis_client.close()
        _redis_client = None


class RedisKeys:
    """Redis key patterns for the application."""

    # API Key caching
    API_KEY_PREFIX = "api_key:"
    API_KEY_HASH_PREFIX = "api_key_hash:"

    # Rate limiting
    RATE_LIMIT_PREFIX = "rate_limit:"
    RATE_LIMIT_TOKENS_PREFIX = "rate_limit_tokens:"

    # Event deduplication
    IDEMPOTENCY_PREFIX = "idempotency:"

    # Subscription caching
    SUBSCRIPTION_PREFIX = "subscription:"
    SUBSCRIPTION_FILTERS_PREFIX = "subscription_filters:"

    @staticmethod
    def api_key(key_hash: str) -> str:
        """Get Redis key for cached API key."""
        return f"{RedisKeys.API_KEY_HASH_PREFIX}{key_hash}"

    @staticmethod
    def rate_limit(api_key_id: str) -> str:
        """Get Redis key for rate limit counter."""
        return f"{RedisKeys.RATE_LIMIT_PREFIX}{api_key_id}"

    @staticmethod
    def rate_limit_tokens(api_key_id: str) -> str:
        """Get Redis key for rate limit token bucket."""
        return f"{RedisKeys.RATE_LIMIT_TOKENS_PREFIX}{api_key_id}"

    @staticmethod
    def idempotency(key: str) -> str:
        """Get Redis key for idempotency check."""
        return f"{RedisKeys.IDEMPOTENCY_PREFIX}{key}"

    @staticmethod
    def subscription(subscription_id: str) -> str:
        """Get Redis key for cached subscription."""
        return f"{RedisKeys.SUBSCRIPTION_PREFIX}{subscription_id}"
