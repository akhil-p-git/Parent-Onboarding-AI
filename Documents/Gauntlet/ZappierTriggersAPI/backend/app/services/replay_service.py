"""
Event Replay Service.

Handles replaying events for debugging and recovery scenarios.
"""

import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.utils import generate_prefixed_id
from app.models import Event, EventStatus, Subscription
from app.models.event_delivery import EventDelivery, DeliveryStatus
from app.services.queue_service import QueueService

logger = logging.getLogger(__name__)


class ReplayError(Exception):
    """Base exception for replay errors."""

    def __init__(self, message: str, code: str = "replay_error"):
        self.message = message
        self.code = code
        super().__init__(message)


class EventNotFoundError(ReplayError):
    """Raised when the event to replay is not found."""

    def __init__(self, event_id: str):
        super().__init__(
            message=f"Event with ID '{event_id}' not found",
            code="event_not_found",
        )


class EventNotReplayableError(ReplayError):
    """Raised when an event cannot be replayed."""

    def __init__(self, event_id: str, reason: str):
        super().__init__(
            message=f"Event '{event_id}' cannot be replayed: {reason}",
            code="event_not_replayable",
        )


class SubscriptionNotFoundError(ReplayError):
    """Raised when a target subscription is not found."""

    def __init__(self, subscription_id: str):
        super().__init__(
            message=f"Subscription with ID '{subscription_id}' not found",
            code="subscription_not_found",
        )


class ReplayResult:
    """Result of a replay operation."""

    def __init__(
        self,
        success: bool,
        event_id: str,
        replay_event_id: str | None = None,
        dry_run: bool = False,
        target_subscriptions: list[str] | None = None,
        message: str | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.success = success
        self.event_id = event_id
        self.replay_event_id = replay_event_id
        self.dry_run = dry_run
        self.target_subscriptions = target_subscriptions or []
        self.message = message
        self.details = details or {}

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "success": self.success,
            "event_id": self.event_id,
            "replay_event_id": self.replay_event_id,
            "dry_run": self.dry_run,
            "target_subscriptions": self.target_subscriptions,
            "message": self.message,
            "details": self.details,
        }


class ReplayService:
    """Service for event replay operations."""

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db
        self.queue_service = QueueService()

    async def replay_event(
        self,
        event_id: str,
        dry_run: bool = False,
        target_subscription_ids: list[str] | None = None,
        payload_override: dict[str, Any] | None = None,
        metadata_override: dict[str, Any] | None = None,
        api_key_id: str | None = None,
    ) -> ReplayResult:
        """
        Replay an event for delivery.

        Args:
            event_id: ID of the event to replay
            dry_run: If True, simulate replay without actually queuing
            target_subscription_ids: Optional list of subscription IDs to target
            payload_override: Optional payload modifications
            metadata_override: Optional metadata modifications
            api_key_id: ID of the API key initiating the replay

        Returns:
            ReplayResult: Result of the replay operation

        Raises:
            EventNotFoundError: If the event is not found
            EventNotReplayableError: If the event cannot be replayed
            SubscriptionNotFoundError: If a target subscription is not found
        """
        # Fetch the original event
        original_event = await self._get_event(event_id)
        if not original_event:
            raise EventNotFoundError(event_id)

        # Validate the event can be replayed
        self._validate_replayable(original_event)

        # Validate and resolve target subscriptions
        target_subscriptions = await self._resolve_subscriptions(
            original_event,
            target_subscription_ids,
        )

        # Build the replayed event payload
        replay_data = self._build_replay_data(
            original_event,
            payload_override,
            metadata_override,
        )

        # Dry run mode - just return what would happen
        if dry_run:
            return ReplayResult(
                success=True,
                event_id=event_id,
                replay_event_id=None,
                dry_run=True,
                target_subscriptions=[s.id for s in target_subscriptions],
                message="Dry run completed. Event would be replayed to matching subscriptions.",
                details={
                    "original_event_type": original_event.event_type,
                    "original_source": original_event.source,
                    "payload_modified": payload_override is not None,
                    "metadata_modified": metadata_override is not None,
                    "matching_subscriptions_count": len(target_subscriptions),
                    "matching_subscriptions": [
                        {
                            "id": s.id,
                            "name": s.name,
                            "webhook_url": s.webhook_url,
                        }
                        for s in target_subscriptions
                    ],
                    "replay_data": replay_data,
                },
            )

        # Create replay event
        replay_event = await self._create_replay_event(
            original_event,
            replay_data,
            api_key_id,
        )

        # Queue for delivery
        await self._queue_replay_event(replay_event, target_subscriptions)

        logger.info(
            f"Replayed event {event_id} as {replay_event.id} "
            f"to {len(target_subscriptions)} subscription(s)"
        )

        return ReplayResult(
            success=True,
            event_id=event_id,
            replay_event_id=replay_event.id,
            dry_run=False,
            target_subscriptions=[s.id for s in target_subscriptions],
            message=f"Event replayed successfully. New event ID: {replay_event.id}",
            details={
                "original_event_type": original_event.event_type,
                "original_source": original_event.source,
                "payload_modified": payload_override is not None,
                "metadata_modified": metadata_override is not None,
                "target_subscriptions_count": len(target_subscriptions),
            },
        )

    async def get_replay_preview(
        self,
        event_id: str,
        target_subscription_ids: list[str] | None = None,
        payload_override: dict[str, Any] | None = None,
        metadata_override: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Get a preview of what a replay would do.

        Args:
            event_id: ID of the event to preview replay for
            target_subscription_ids: Optional list of subscription IDs to target
            payload_override: Optional payload modifications
            metadata_override: Optional metadata modifications

        Returns:
            dict: Preview of replay operation
        """
        original_event = await self._get_event(event_id)
        if not original_event:
            raise EventNotFoundError(event_id)

        target_subscriptions = await self._resolve_subscriptions(
            original_event,
            target_subscription_ids,
        )

        replay_data = self._build_replay_data(
            original_event,
            payload_override,
            metadata_override,
        )

        return {
            "event_id": event_id,
            "original_event": {
                "id": original_event.id,
                "event_type": original_event.event_type,
                "source": original_event.source,
                "status": original_event.status.value,
                "created_at": original_event.created_at.isoformat() if original_event.created_at else None,
                "delivery_attempts": original_event.delivery_attempts,
            },
            "replay_payload": replay_data,
            "target_subscriptions": [
                {
                    "id": s.id,
                    "name": s.name,
                    "webhook_url": s.webhook_url,
                    "event_types": s.event_types,
                }
                for s in target_subscriptions
            ],
            "modifications": {
                "payload_override": payload_override,
                "metadata_override": metadata_override,
            },
        }

    async def _get_event(self, event_id: str) -> Event | None:
        """Fetch an event by ID."""
        result = await self.db.execute(
            select(Event).where(Event.id == event_id)
        )
        return result.scalar_one_or_none()

    def _validate_replayable(self, event: Event) -> None:
        """Validate that an event can be replayed."""
        # Check if event is expired
        if event.status == EventStatus.EXPIRED:
            raise EventNotReplayableError(
                event.id,
                "Event has expired and cannot be replayed",
            )

        # Check if replay is enabled
        if not settings.ENABLE_EVENT_REPLAY:
            raise EventNotReplayableError(
                event.id,
                "Event replay feature is disabled",
            )

    async def _resolve_subscriptions(
        self,
        event: Event,
        target_subscription_ids: list[str] | None,
    ) -> list[Subscription]:
        """
        Resolve target subscriptions for replay.

        If specific IDs are provided, validate and return those.
        Otherwise, find all matching subscriptions for the event type.
        """
        if target_subscription_ids:
            # Fetch specific subscriptions
            subscriptions = []
            for sub_id in target_subscription_ids:
                result = await self.db.execute(
                    select(Subscription).where(
                        Subscription.id == sub_id,
                        Subscription.is_active == True,
                    )
                )
                subscription = result.scalar_one_or_none()
                if not subscription:
                    raise SubscriptionNotFoundError(sub_id)
                subscriptions.append(subscription)
            return subscriptions
        else:
            # Find all matching subscriptions
            result = await self.db.execute(
                select(Subscription).where(
                    Subscription.is_active == True,
                )
            )
            all_subscriptions = result.scalars().all()

            # Filter by event type match
            matching = []
            for sub in all_subscriptions:
                if self._subscription_matches_event(sub, event):
                    matching.append(sub)

            return matching

    def _subscription_matches_event(
        self,
        subscription: Subscription,
        event: Event,
    ) -> bool:
        """Check if a subscription matches an event type."""
        # If no event_types filter, match all
        if not subscription.event_types:
            return True

        # Check for exact match or wildcard
        for pattern in subscription.event_types:
            if pattern == "*":
                return True
            if pattern == event.event_type:
                return True
            # Support prefix wildcard (e.g., "user.*" matches "user.created")
            if pattern.endswith(".*"):
                prefix = pattern[:-2]
                if event.event_type.startswith(prefix + "."):
                    return True

        return False

    def _build_replay_data(
        self,
        original_event: Event,
        payload_override: dict[str, Any] | None,
        metadata_override: dict[str, Any] | None,
    ) -> dict[str, Any]:
        """Build the replay event data."""
        # Start with original data
        data = dict(original_event.data) if original_event.data else {}

        # Apply payload overrides (merge)
        if payload_override:
            data = self._deep_merge(data, payload_override)

        # Build metadata
        metadata = dict(original_event.event_meta) if original_event.event_meta else {}

        # Add replay tracking metadata
        metadata["_replay"] = {
            "original_event_id": original_event.id,
            "replayed_at": datetime.now(timezone.utc).isoformat(),
        }

        # Apply metadata overrides (merge)
        if metadata_override:
            metadata = self._deep_merge(metadata, metadata_override)

        return {
            "event_type": original_event.event_type,
            "source": original_event.source,
            "data": data,
            "metadata": metadata,
        }

    def _deep_merge(
        self,
        base: dict[str, Any],
        override: dict[str, Any],
    ) -> dict[str, Any]:
        """Deep merge two dictionaries."""
        result = dict(base)
        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        return result

    async def _create_replay_event(
        self,
        original_event: Event,
        replay_data: dict[str, Any],
        api_key_id: str | None,
    ) -> Event:
        """Create a new event for the replay."""
        replay_event = Event(
            id=generate_prefixed_id("evt"),
            event_type=replay_data["event_type"],
            source=replay_data["source"],
            data=replay_data["data"],
            metadata=replay_data["metadata"],
            status=EventStatus.PENDING,
            api_key_id=api_key_id,
            # No idempotency key for replays - each replay creates a new event
        )

        self.db.add(replay_event)
        await self.db.flush()

        return replay_event

    async def _queue_replay_event(
        self,
        event: Event,
        target_subscriptions: list[Subscription],
    ) -> None:
        """Queue the replay event for delivery."""
        # If targeting specific subscriptions, create delivery records
        if target_subscriptions:
            for subscription in target_subscriptions:
                delivery = EventDelivery(
                    id=generate_prefixed_id("del"),
                    event_id=event.id,
                    subscription_id=subscription.id,
                    status=DeliveryStatus.PENDING,
                    webhook_url=subscription.webhook_url,
                )
                self.db.add(delivery)

            await self.db.flush()

        # Enqueue for processing
        await self.queue_service.enqueue_event(event)
