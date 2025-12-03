"""
API Key Service.

Handles API key generation, validation, and management.
"""

import json
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import RedisKeys, get_redis
from app.core.security import (
    extract_key_prefix,
    generate_api_key,
    hash_api_key,
    is_key_expired,
    mask_api_key,
)
from app.models import ApiKey, ApiKeyEnvironment, ApiKeyScope, DEFAULT_SCOPES


class ApiKeyService:
    """Service for API key operations."""

    # Cache TTL for API keys (5 minutes)
    CACHE_TTL = 300

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db

    async def create_api_key(
        self,
        name: str,
        environment: ApiKeyEnvironment = ApiKeyEnvironment.TEST,
        scopes: list[str] | None = None,
        description: str | None = None,
        expires_at: datetime | None = None,
        rate_limit: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> tuple[ApiKey, str]:
        """
        Create a new API key.

        Args:
            name: Human-readable name for the key
            environment: live or test environment
            scopes: List of permission scopes
            description: Optional description
            expires_at: Optional expiration datetime
            rate_limit: Optional custom rate limit
            metadata: Optional metadata

        Returns:
            tuple: (ApiKey model, raw API key string)
            Note: The raw key is only returned once and should be shown to the user
        """
        # Generate the raw API key
        raw_key = generate_api_key(environment.value)

        # Hash for storage
        key_hash = hash_api_key(raw_key)

        # Extract prefix for identification
        key_prefix = extract_key_prefix(raw_key)

        # Use default scopes if not specified
        if scopes is None:
            scopes = [s.value for s in DEFAULT_SCOPES]

        # Create the API key record
        api_key = ApiKey(
            name=name,
            description=description,
            key_hash=key_hash,
            key_prefix=key_prefix,
            environment=environment,
            scopes=scopes,
            expires_at=expires_at,
            rate_limit=rate_limit,
            extra_data=metadata,
        )

        self.db.add(api_key)
        await self.db.flush()

        return api_key, raw_key

    async def validate_api_key(self, raw_key: str) -> ApiKey | None:
        """
        Validate an API key and return the associated record.

        First checks Redis cache, then falls back to database.

        Args:
            raw_key: The raw API key from the request

        Returns:
            ApiKey | None: The API key record if valid, None otherwise
        """
        key_hash = hash_api_key(raw_key)

        # Try cache first
        cached = await self._get_cached_key(key_hash)
        if cached is not None:
            if cached == "invalid":
                return None
            return cached

        # Query database
        result = await self.db.execute(
            select(ApiKey).where(ApiKey.key_hash == key_hash)
        )
        api_key = result.scalar_one_or_none()

        # Cache the result
        if api_key is None:
            await self._cache_invalid_key(key_hash)
            return None

        # Check if key is valid
        if not api_key.is_valid:
            await self._cache_invalid_key(key_hash)
            return None

        # Cache valid key
        await self._cache_api_key(api_key)

        return api_key

    async def get_api_key(self, key_id: str) -> ApiKey | None:
        """
        Get an API key by ID.

        Args:
            key_id: The API key ID

        Returns:
            ApiKey | None: The API key record if found
        """
        result = await self.db.execute(
            select(ApiKey).where(ApiKey.id == key_id)
        )
        return result.scalar_one_or_none()

    async def list_api_keys(
        self,
        environment: ApiKeyEnvironment | None = None,
        is_active: bool | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> list[ApiKey]:
        """
        List API keys with optional filters.

        Args:
            environment: Filter by environment
            is_active: Filter by active status
            limit: Max results to return
            offset: Pagination offset

        Returns:
            list[ApiKey]: List of API keys
        """
        query = select(ApiKey).order_by(ApiKey.created_at.desc())

        if environment is not None:
            query = query.where(ApiKey.environment == environment)

        if is_active is not None:
            query = query.where(ApiKey.is_active == is_active)

        query = query.limit(limit).offset(offset)

        result = await self.db.execute(query)
        return list(result.scalars().all())

    async def update_api_key(
        self,
        key_id: str,
        name: str | None = None,
        description: str | None = None,
        scopes: list[str] | None = None,
        is_active: bool | None = None,
        rate_limit: int | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> ApiKey | None:
        """
        Update an API key.

        Args:
            key_id: The API key ID
            name: New name
            description: New description
            scopes: New scopes
            is_active: New active status
            rate_limit: New rate limit
            metadata: New metadata

        Returns:
            ApiKey | None: Updated API key or None if not found
        """
        api_key = await self.get_api_key(key_id)
        if api_key is None:
            return None

        if name is not None:
            api_key.name = name
        if description is not None:
            api_key.description = description
        if scopes is not None:
            api_key.scopes = scopes
        if is_active is not None:
            api_key.is_active = is_active
        if rate_limit is not None:
            api_key.rate_limit = rate_limit
        if metadata is not None:
            api_key.extra_data = metadata

        await self.db.flush()

        # Invalidate cache
        await self._invalidate_cache(api_key.key_hash)

        return api_key

    async def revoke_api_key(
        self,
        key_id: str,
        reason: str | None = None,
    ) -> ApiKey | None:
        """
        Revoke an API key.

        Args:
            key_id: The API key ID
            reason: Optional reason for revocation

        Returns:
            ApiKey | None: Revoked API key or None if not found
        """
        api_key = await self.get_api_key(key_id)
        if api_key is None:
            return None

        api_key.is_active = False
        api_key.revoked_at = datetime.now(timezone.utc)
        api_key.revoked_reason = reason

        await self.db.flush()

        # Invalidate cache
        await self._invalidate_cache(api_key.key_hash)

        return api_key

    async def record_usage(self, api_key: ApiKey) -> None:
        """
        Record API key usage.

        Args:
            api_key: The API key that was used
        """
        api_key.last_used_at = datetime.now(timezone.utc)
        api_key.usage_count += 1
        await self.db.flush()

    async def _get_cached_key(self, key_hash: str) -> ApiKey | str | None:
        """
        Get API key from cache.

        Returns:
            ApiKey if cached and valid
            "invalid" if cached as invalid
            None if not cached
        """
        try:
            redis = await get_redis()
            cache_key = RedisKeys.api_key(key_hash)
            cached = await redis.get(cache_key)

            if cached is None:
                return None

            if cached == "invalid":
                return "invalid"

            # Deserialize and reconstruct ApiKey
            data = json.loads(cached)
            api_key = ApiKey(
                id=data["id"],
                name=data["name"],
                key_hash=data["key_hash"],
                key_prefix=data["key_prefix"],
                environment=ApiKeyEnvironment(data["environment"]),
                scopes=data["scopes"],
                is_active=data["is_active"],
                rate_limit=data.get("rate_limit"),
            )
            # Set expiration if present
            if data.get("expires_at"):
                api_key.expires_at = datetime.fromisoformat(data["expires_at"])

            return api_key

        except Exception:
            # Cache failures should not break authentication
            return None

    async def _cache_api_key(self, api_key: ApiKey) -> None:
        """Cache a valid API key."""
        try:
            redis = await get_redis()
            cache_key = RedisKeys.api_key(api_key.key_hash)

            data = {
                "id": api_key.id,
                "name": api_key.name,
                "key_hash": api_key.key_hash,
                "key_prefix": api_key.key_prefix,
                "environment": api_key.environment.value,
                "scopes": api_key.scopes,
                "is_active": api_key.is_active,
                "rate_limit": api_key.rate_limit,
                "expires_at": api_key.expires_at.isoformat() if api_key.expires_at else None,
            }

            await redis.setex(cache_key, self.CACHE_TTL, json.dumps(data))

        except Exception:
            # Cache failures should not break authentication
            pass

    async def _cache_invalid_key(self, key_hash: str) -> None:
        """Cache an invalid key hash to prevent repeated DB lookups."""
        try:
            redis = await get_redis()
            cache_key = RedisKeys.api_key(key_hash)
            # Cache invalid keys for shorter duration
            await redis.setex(cache_key, 60, "invalid")
        except Exception:
            pass

    async def _invalidate_cache(self, key_hash: str) -> None:
        """Invalidate cached API key."""
        try:
            redis = await get_redis()
            cache_key = RedisKeys.api_key(key_hash)
            await redis.delete(cache_key)
        except Exception:
            pass


def get_masked_key(api_key: ApiKey) -> str:
    """
    Get masked version of an API key for display.

    Args:
        api_key: The API key record

    Returns:
        str: Masked key prefix
    """
    return f"{api_key.key_prefix}...****"
