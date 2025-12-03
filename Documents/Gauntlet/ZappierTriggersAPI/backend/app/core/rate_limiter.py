"""
Rate Limiting Middleware.

Implements token bucket rate limiting using Redis.
"""

import time
from dataclasses import dataclass
from typing import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

from app.core.config import settings
from app.core.redis import RedisKeys, get_redis


@dataclass
class RateLimitResult:
    """Result of a rate limit check."""

    allowed: bool
    limit: int
    remaining: int
    reset_at: int
    retry_after: int | None = None


class TokenBucketRateLimiter:
    """
    Token bucket rate limiter using Redis.

    The token bucket algorithm:
    - Bucket starts full with `capacity` tokens
    - Each request consumes one token
    - Tokens are refilled at `rate` tokens per second
    - If bucket is empty, request is rejected
    """

    def __init__(
        self,
        rate: float,
        capacity: int,
        key_prefix: str = "rate_limit",
    ):
        """
        Initialize rate limiter.

        Args:
            rate: Tokens added per second
            capacity: Maximum tokens in bucket (burst limit)
            key_prefix: Redis key prefix
        """
        self.rate = rate
        self.capacity = capacity
        self.key_prefix = key_prefix

    async def check(self, identifier: str) -> RateLimitResult:
        """
        Check if request is allowed under rate limit.

        Uses Redis to track token bucket state atomically.

        Args:
            identifier: Unique identifier (e.g., API key ID, IP address)

        Returns:
            RateLimitResult: Whether request is allowed and limit info
        """
        redis = await get_redis()
        now = time.time()

        # Redis keys for this identifier
        tokens_key = f"{self.key_prefix}:tokens:{identifier}"
        timestamp_key = f"{self.key_prefix}:ts:{identifier}"

        # Lua script for atomic token bucket operation
        lua_script = """
        local tokens_key = KEYS[1]
        local timestamp_key = KEYS[2]
        local rate = tonumber(ARGV[1])
        local capacity = tonumber(ARGV[2])
        local now = tonumber(ARGV[3])
        local ttl = tonumber(ARGV[4])

        -- Get current state
        local last_tokens = tonumber(redis.call('GET', tokens_key) or capacity)
        local last_time = tonumber(redis.call('GET', timestamp_key) or now)

        -- Calculate tokens to add based on time elapsed
        local elapsed = math.max(0, now - last_time)
        local add_tokens = elapsed * rate
        local current_tokens = math.min(capacity, last_tokens + add_tokens)

        -- Check if we can consume a token
        local allowed = 0
        local new_tokens = current_tokens

        if current_tokens >= 1 then
            allowed = 1
            new_tokens = current_tokens - 1
        end

        -- Update state
        redis.call('SETEX', tokens_key, ttl, new_tokens)
        redis.call('SETEX', timestamp_key, ttl, now)

        -- Calculate reset time (when bucket will be full)
        local tokens_needed = capacity - new_tokens
        local reset_seconds = tokens_needed / rate
        local reset_at = math.ceil(now + reset_seconds)

        return {allowed, math.floor(new_tokens), reset_at}
        """

        # Execute atomically
        result = await redis.eval(
            lua_script,
            2,  # number of keys
            tokens_key,
            timestamp_key,
            self.rate,
            self.capacity,
            now,
            3600,  # TTL in seconds (1 hour)
        )

        allowed = bool(result[0])
        remaining = int(result[1])
        reset_at = int(result[2])

        return RateLimitResult(
            allowed=allowed,
            limit=self.capacity,
            remaining=remaining,
            reset_at=reset_at,
            retry_after=None if allowed else max(1, reset_at - int(now)),
        )

    async def reset(self, identifier: str) -> None:
        """
        Reset rate limit for an identifier.

        Args:
            identifier: Unique identifier to reset
        """
        redis = await get_redis()
        tokens_key = f"{self.key_prefix}:tokens:{identifier}"
        timestamp_key = f"{self.key_prefix}:ts:{identifier}"
        await redis.delete(tokens_key, timestamp_key)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    FastAPI middleware for rate limiting.

    Applies rate limits based on API key or IP address.
    """

    def __init__(
        self,
        app: ASGIApp,
        default_rate: float | None = None,
        default_capacity: int | None = None,
        exclude_paths: list[str] | None = None,
        get_identifier: Callable[[Request], str] | None = None,
    ):
        """
        Initialize rate limit middleware.

        Args:
            app: FastAPI application
            default_rate: Default tokens per second
            default_capacity: Default bucket capacity
            exclude_paths: Paths to exclude from rate limiting
            get_identifier: Custom function to extract identifier from request
        """
        super().__init__(app)

        # Use settings defaults if not specified
        self.default_rate = default_rate or (settings.RATE_LIMIT_REQUESTS_PER_MINUTE / 60)
        self.default_capacity = default_capacity or settings.RATE_LIMIT_BURST

        self.exclude_paths = exclude_paths or [
            "/health",
            "/ready",
            "/docs",
            "/redoc",
            "/openapi.json",
        ]

        self.get_identifier = get_identifier or self._default_get_identifier
        self.limiter = TokenBucketRateLimiter(
            rate=self.default_rate,
            capacity=self.default_capacity,
        )

    def _default_get_identifier(self, request: Request) -> str:
        """
        Get rate limit identifier from request.

        Uses API key ID if authenticated, otherwise IP address.
        """
        # Check if API key is in request state (set by auth middleware)
        if hasattr(request.state, "api_key") and request.state.api_key:
            return f"key:{request.state.api_key.id}"

        # Fall back to IP address
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            ip = forwarded.split(",")[0].strip()
        else:
            ip = request.client.host if request.client else "unknown"

        return f"ip:{ip}"

    def _should_limit(self, request: Request) -> bool:
        """Check if request should be rate limited."""
        # Skip excluded paths
        for path in self.exclude_paths:
            if request.url.path.startswith(path):
                return False
        return True

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process request with rate limiting."""
        # Skip rate limiting for excluded paths
        if not self._should_limit(request):
            return await call_next(request)

        # Get identifier for rate limiting
        identifier = self.get_identifier(request)

        # Check custom rate limit from API key
        rate = self.default_rate
        capacity = self.default_capacity

        if hasattr(request.state, "api_key") and request.state.api_key:
            api_key = request.state.api_key
            if api_key.rate_limit:
                # Custom rate limit is per minute
                rate = api_key.rate_limit / 60
                capacity = max(api_key.rate_limit // 10, 10)  # Burst = 10% of limit

        # Create limiter with appropriate settings
        limiter = TokenBucketRateLimiter(rate=rate, capacity=capacity)
        result = await limiter.check(identifier)

        # Add rate limit headers to all responses
        response = None

        if not result.allowed:
            # Rate limited - return 429
            from fastapi.responses import JSONResponse

            response = JSONResponse(
                status_code=429,
                content={
                    "error": "rate_limit_exceeded",
                    "message": "Too many requests. Please slow down.",
                    "retry_after": result.retry_after,
                },
                headers={
                    "Retry-After": str(result.retry_after),
                },
            )
        else:
            # Process request
            response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(result.limit)
        response.headers["X-RateLimit-Remaining"] = str(result.remaining)
        response.headers["X-RateLimit-Reset"] = str(result.reset_at)

        return response


# Utility function for manual rate limiting in endpoints
async def check_rate_limit(
    identifier: str,
    rate: float | None = None,
    capacity: int | None = None,
) -> RateLimitResult:
    """
    Manually check rate limit for an identifier.

    Args:
        identifier: Unique identifier
        rate: Tokens per second (default from settings)
        capacity: Bucket capacity (default from settings)

    Returns:
        RateLimitResult: Rate limit check result
    """
    limiter = TokenBucketRateLimiter(
        rate=rate or (settings.RATE_LIMIT_REQUESTS_PER_MINUTE / 60),
        capacity=capacity or settings.RATE_LIMIT_BURST,
    )
    return await limiter.check(identifier)
