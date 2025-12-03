"""
Subscription Service.

Handles webhook subscription management.
"""

import base64
import json
import logging
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import get_redis
from app.core.security import generate_signing_secret
from app.core.utils import generate_prefixed_id
from app.models import Event, Subscription, SubscriptionStatus
from app.schemas import (
    CreateSubscriptionRequest,
    UpdateSubscriptionRequest,
    WebhookConfig,
)

logger = logging.getLogger(__name__)


class SubscriptionService:
    """Service for subscription operations."""

    # Cache TTL for subscriptions (5 minutes)
    CACHE_TTL = 300

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db

    async def create_subscription(
        self,
        request: CreateSubscriptionRequest,
        api_key_id: str | None = None,
    ) -> Subscription:
        """
        Create a new subscription.

        Args:
            request: Subscription creation request
            api_key_id: ID of the API key creating the subscription

        Returns:
            Subscription: The created subscription
        """
        # Generate subscription ID and signing secret
        subscription_id = generate_prefixed_id("sub")
        signing_secret = generate_signing_secret()

        # Extract webhook config
        webhook_config = request.webhook_config or WebhookConfig()

        # Extract filters
        event_types = None
        event_sources = None
        filters = None
        if request.filters:
            event_types = request.filters.event_types
            event_sources = request.filters.event_sources
            filters = request.filters.advanced_filters

        # Create subscription record
        subscription = Subscription(
            id=subscription_id,
            name=request.name,
            description=request.description,
            target_url=request.target_url,
            signing_secret=signing_secret,
            custom_headers=request.custom_headers,
            event_types=event_types,
            event_sources=event_sources,
            filters=filters,
            status=SubscriptionStatus.ACTIVE,
            retry_strategy=webhook_config.retry_strategy,
            max_retries=webhook_config.max_retries,
            retry_delay_seconds=webhook_config.retry_delay_seconds,
            retry_max_delay_seconds=webhook_config.retry_max_delay_seconds,
            timeout_seconds=webhook_config.timeout_seconds,
            api_key_id=api_key_id,
            sub_meta=request.metadata,
        )

        self.db.add(subscription)
        await self.db.flush()

        logger.info(f"Created subscription {subscription_id} for {request.target_url}")

        return subscription

    async def get_subscription(self, subscription_id: str) -> Subscription | None:
        """
        Get a subscription by ID.

        Args:
            subscription_id: The subscription ID

        Returns:
            Subscription | None: The subscription if found
        """
        result = await self.db.execute(
            select(Subscription).where(
                and_(
                    Subscription.id == subscription_id,
                    Subscription.deleted_at.is_(None),
                )
            )
        )
        return result.scalar_one_or_none()

    async def list_subscriptions(
        self,
        status: SubscriptionStatus | None = None,
        is_healthy: bool | None = None,
        api_key_id: str | None = None,
        limit: int = 100,
        cursor: str | None = None,
    ) -> tuple[list[Subscription], str | None]:
        """
        List subscriptions with optional filters.

        Args:
            status: Filter by status
            is_healthy: Filter by health status
            api_key_id: Filter by API key
            limit: Maximum subscriptions to return
            cursor: Pagination cursor

        Returns:
            tuple: (list of subscriptions, next cursor or None)
        """
        query = (
            select(Subscription)
            .where(Subscription.deleted_at.is_(None))
            .order_by(Subscription.created_at.desc())
        )

        if status:
            query = query.where(Subscription.status == status)
        if is_healthy is not None:
            query = query.where(Subscription.is_healthy == is_healthy)
        if api_key_id:
            query = query.where(Subscription.api_key_id == api_key_id)

        # Handle cursor pagination
        if cursor:
            try:
                cursor_data = json.loads(base64.b64decode(cursor).decode())
                cursor_id = cursor_data.get("id")
                if cursor_id:
                    query = query.where(Subscription.id < cursor_id)
            except Exception:
                pass

        query = query.limit(limit + 1)

        result = await self.db.execute(query)
        subscriptions = list(result.scalars().all())

        # Determine next cursor
        next_cursor = None
        if len(subscriptions) > limit:
            subscriptions = subscriptions[:limit]
            last = subscriptions[-1]
            cursor_data = {"id": last.id}
            next_cursor = base64.b64encode(
                json.dumps(cursor_data).encode()
            ).decode()

        return subscriptions, next_cursor

    async def update_subscription(
        self,
        subscription_id: str,
        request: UpdateSubscriptionRequest,
    ) -> Subscription | None:
        """
        Update a subscription.

        Args:
            subscription_id: The subscription ID
            request: Update request

        Returns:
            Subscription | None: Updated subscription or None if not found
        """
        subscription = await self.get_subscription(subscription_id)
        if not subscription:
            return None

        # Update fields if provided
        if request.name is not None:
            subscription.name = request.name
        if request.description is not None:
            subscription.description = request.description
        if request.target_url is not None:
            subscription.target_url = request.target_url
        if request.custom_headers is not None:
            subscription.custom_headers = request.custom_headers
        if request.status is not None:
            subscription.status = request.status
        if request.metadata is not None:
            subscription.sub_meta = request.metadata

        # Update filters
        if request.filters is not None:
            subscription.event_types = request.filters.event_types
            subscription.event_sources = request.filters.event_sources
            subscription.filters = request.filters.advanced_filters

        # Update webhook config
        if request.webhook_config is not None:
            subscription.retry_strategy = request.webhook_config.retry_strategy
            subscription.max_retries = request.webhook_config.max_retries
            subscription.retry_delay_seconds = request.webhook_config.retry_delay_seconds
            subscription.retry_max_delay_seconds = request.webhook_config.retry_max_delay_seconds
            subscription.timeout_seconds = request.webhook_config.timeout_seconds

        await self.db.flush()

        # Invalidate cache
        await self._invalidate_cache(subscription_id)

        logger.info(f"Updated subscription {subscription_id}")

        return subscription

    async def delete_subscription(self, subscription_id: str) -> bool:
        """
        Soft delete a subscription.

        Args:
            subscription_id: The subscription ID

        Returns:
            bool: Whether deletion was successful
        """
        subscription = await self.get_subscription(subscription_id)
        if not subscription:
            return False

        subscription.status = SubscriptionStatus.DELETED
        subscription.deleted_at = datetime.now(timezone.utc)

        await self.db.flush()

        # Invalidate cache
        await self._invalidate_cache(subscription_id)

        logger.info(f"Deleted subscription {subscription_id}")

        return True

    async def rotate_signing_secret(
        self,
        subscription_id: str,
        grace_period_hours: int = 24,
    ) -> tuple[str, datetime] | None:
        """
        Rotate the signing secret for a subscription.

        Args:
            subscription_id: The subscription ID
            grace_period_hours: Hours the old secret remains valid

        Returns:
            tuple | None: (new secret, old secret expiry) or None if not found
        """
        subscription = await self.get_subscription(subscription_id)
        if not subscription:
            return None

        # Store old secret in metadata for grace period
        old_secret = subscription.signing_secret
        old_secret_expiry = datetime.now(timezone.utc) + timedelta(hours=grace_period_hours)

        metadata = subscription.sub_meta or {}
        metadata["previous_signing_secret"] = old_secret
        metadata["previous_secret_valid_until"] = old_secret_expiry.isoformat()

        # Generate new secret
        new_secret = generate_signing_secret()
        subscription.signing_secret = new_secret
        subscription.sub_meta = metadata

        await self.db.flush()

        # Invalidate cache
        await self._invalidate_cache(subscription_id)

        logger.info(f"Rotated signing secret for subscription {subscription_id}")

        return new_secret, old_secret_expiry

    async def get_matching_subscriptions(
        self,
        event: Event,
    ) -> list[Subscription]:
        """
        Get subscriptions that match an event.

        Args:
            event: The event to match

        Returns:
            list: Matching active subscriptions
        """
        # Get all active subscriptions
        query = select(Subscription).where(
            and_(
                Subscription.status == SubscriptionStatus.ACTIVE,
                Subscription.is_healthy == True,
                Subscription.deleted_at.is_(None),
            )
        )

        result = await self.db.execute(query)
        subscriptions = list(result.scalars().all())

        # Filter by event type and source
        matching = []
        for sub in subscriptions:
            if sub.matches_event(event.event_type, event.source):
                matching.append(sub)

        return matching

    async def pause_subscription(self, subscription_id: str) -> bool:
        """Pause a subscription (stop deliveries)."""
        subscription = await self.get_subscription(subscription_id)
        if not subscription:
            return False

        subscription.status = SubscriptionStatus.PAUSED
        await self.db.flush()
        await self._invalidate_cache(subscription_id)

        return True

    async def resume_subscription(self, subscription_id: str) -> bool:
        """Resume a paused subscription."""
        subscription = await self.get_subscription(subscription_id)
        if not subscription:
            return False

        if subscription.status != SubscriptionStatus.PAUSED:
            return False

        subscription.status = SubscriptionStatus.ACTIVE
        await self.db.flush()
        await self._invalidate_cache(subscription_id)

        return True

    async def get_stats(self) -> dict[str, int]:
        """Get subscription statistics."""
        from sqlalchemy import func

        result = await self.db.execute(
            select(
                Subscription.status,
                Subscription.is_healthy,
                func.count(Subscription.id),
            )
            .where(Subscription.deleted_at.is_(None))
            .group_by(Subscription.status, Subscription.is_healthy)
        )

        stats = {
            "total_subscriptions": 0,
            "active": 0,
            "paused": 0,
            "disabled": 0,
            "healthy": 0,
            "unhealthy": 0,
        }

        for status, is_healthy, count in result:
            stats["total_subscriptions"] += count

            if status == SubscriptionStatus.ACTIVE:
                stats["active"] += count
            elif status == SubscriptionStatus.PAUSED:
                stats["paused"] += count
            elif status == SubscriptionStatus.DISABLED:
                stats["disabled"] += count

            if is_healthy:
                stats["healthy"] += count
            else:
                stats["unhealthy"] += count

        return stats

    async def _invalidate_cache(self, subscription_id: str) -> None:
        """Invalidate cached subscription."""
        try:
            redis = await get_redis()
            await redis.delete(f"subscription:{subscription_id}")
        except Exception as e:
            logger.warning(f"Redis error invalidating cache: {e}")
