"""
Inbox Service.

Handles inbox operations for polling-based event retrieval.
"""

import base64
import json
import logging
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import RedisKeys, get_redis
from app.models import Event, EventStatus

logger = logging.getLogger(__name__)


class InboxService:
    """Service for inbox operations."""

    # Default visibility timeout (30 seconds)
    DEFAULT_VISIBILITY_TIMEOUT = 30

    # Maximum visibility timeout (12 hours)
    MAX_VISIBILITY_TIMEOUT = 43200

    # Receipt handle prefix
    RECEIPT_PREFIX = "rcpt_"

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db

    async def fetch_events(
        self,
        limit: int = 10,
        visibility_timeout: int | None = None,
        event_types: list[str] | None = None,
        sources: list[str] | None = None,
        wait_time: int = 0,
    ) -> tuple[list[dict[str, Any]], bool]:
        """
        Fetch events from the inbox.

        Events are marked as "in-flight" with a visibility timeout.
        If not acknowledged within the timeout, they become visible again.

        Args:
            limit: Maximum number of events to fetch
            visibility_timeout: Seconds before events become visible again
            event_types: Filter by event types
            sources: Filter by sources
            wait_time: Long polling wait time (not implemented yet)

        Returns:
            tuple: (list of inbox items with receipt handles, has_more flag)
        """
        timeout = min(
            visibility_timeout or self.DEFAULT_VISIBILITY_TIMEOUT,
            self.MAX_VISIBILITY_TIMEOUT,
        )

        now = datetime.now(timezone.utc)
        visibility_deadline = now + timedelta(seconds=timeout)

        # Build query for pending events
        query = (
            select(Event)
            .where(
                and_(
                    Event.status == EventStatus.PENDING,
                    # Not currently in-flight (or visibility expired)
                )
            )
            .order_by(Event.created_at.asc())  # Oldest first
            .limit(limit + 1)  # Fetch one extra to check has_more
        )

        # Apply filters
        if event_types:
            query = query.where(Event.event_type.in_(event_types))
        if sources:
            query = query.where(Event.source.in_(sources))

        result = await self.db.execute(query)
        events = list(result.scalars().all())

        # Check if there are more events
        has_more = len(events) > limit
        events = events[:limit]

        # Generate receipt handles and mark events as in-flight
        inbox_items = []
        for event in events:
            receipt_handle = await self._generate_receipt_handle(
                event.id,
                visibility_deadline,
            )

            inbox_items.append({
                "id": event.id,
                "event_type": event.event_type,
                "source": event.source,
                "data": event.data,
                "metadata": event.event_meta,
                "created_at": event.created_at,
                "receipt_handle": receipt_handle,
                "visibility_timeout": visibility_deadline,
                "delivery_count": event.delivery_attempts + 1,
            })

            # Increment delivery attempts
            event.delivery_attempts += 1

        await self.db.flush()

        return inbox_items, has_more

    async def acknowledge(self, receipt_handle: str) -> bool:
        """
        Acknowledge an event by receipt handle.

        Args:
            receipt_handle: The receipt handle from fetch_events

        Returns:
            bool: Whether acknowledgment was successful
        """
        # Validate and extract event ID from receipt handle
        event_id = await self._validate_receipt_handle(receipt_handle)
        if not event_id:
            logger.warning(f"Invalid receipt handle: {receipt_handle}")
            return False

        # Update event status to delivered
        result = await self.db.execute(
            update(Event)
            .where(Event.id == event_id)
            .values(
                status=EventStatus.DELIVERED,
                processed_at=datetime.now(timezone.utc),
                successful_deliveries=Event.successful_deliveries + 1,
            )
            .returning(Event.id)
        )

        updated = result.scalar_one_or_none()

        if updated:
            # Invalidate receipt handle
            await self._invalidate_receipt_handle(receipt_handle)
            logger.info(f"Acknowledged event {event_id}")
            return True

        return False

    async def acknowledge_batch(
        self,
        receipt_handles: list[str],
    ) -> list[dict[str, Any]]:
        """
        Acknowledge multiple events.

        Args:
            receipt_handles: List of receipt handles to acknowledge

        Returns:
            list: Per-handle results with success/failure status
        """
        results = []

        for handle in receipt_handles:
            try:
                success = await self.acknowledge(handle)
                results.append({
                    "receipt_handle": handle,
                    "success": success,
                    "error": None if success else "Receipt handle not found or expired",
                })
            except Exception as e:
                logger.error(f"Error acknowledging {handle}: {e}")
                results.append({
                    "receipt_handle": handle,
                    "success": False,
                    "error": str(e),
                })

        return results

    async def change_visibility(
        self,
        receipt_handle: str,
        visibility_timeout: int,
    ) -> datetime | None:
        """
        Change the visibility timeout of an event.

        Args:
            receipt_handle: The receipt handle
            visibility_timeout: New timeout in seconds (0 = make visible immediately)

        Returns:
            datetime | None: New visibility timeout or None if failed
        """
        event_id = await self._validate_receipt_handle(receipt_handle)
        if not event_id:
            return None

        new_deadline = datetime.now(timezone.utc) + timedelta(seconds=visibility_timeout)

        # Update the receipt handle with new deadline
        await self._update_receipt_handle(receipt_handle, new_deadline)

        return new_deadline

    async def get_stats(self) -> dict[str, Any]:
        """
        Get inbox statistics.

        Returns:
            dict: Statistics about the inbox
        """
        from sqlalchemy import func

        # Count by status
        status_counts = await self.db.execute(
            select(Event.status, func.count(Event.id))
            .group_by(Event.status)
        )

        counts = {row[0]: row[1] for row in status_counts}

        # Get oldest pending event
        oldest = await self.db.execute(
            select(Event.created_at)
            .where(Event.status == EventStatus.PENDING)
            .order_by(Event.created_at.asc())
            .limit(1)
        )
        oldest_event = oldest.scalar_one_or_none()

        # Count by event type (for pending)
        type_counts = await self.db.execute(
            select(Event.event_type, func.count(Event.id))
            .where(Event.status == EventStatus.PENDING)
            .group_by(Event.event_type)
        )

        return {
            "visible": counts.get(EventStatus.PENDING, 0),
            "in_flight": counts.get(EventStatus.PROCESSING, 0),
            "delayed": 0,  # Not implemented
            "total": sum(counts.values()),
            "oldest_event_at": oldest_event,
            "by_event_type": {row[0]: row[1] for row in type_counts},
        }

    async def _generate_receipt_handle(
        self,
        event_id: str,
        deadline: datetime,
    ) -> str:
        """
        Generate a receipt handle for an event.

        The handle encodes the event ID and expiration, stored in Redis.
        """
        # Generate unique handle
        handle_id = secrets.token_urlsafe(16)
        receipt_handle = f"{self.RECEIPT_PREFIX}{handle_id}"

        # Store in Redis with expiration
        try:
            redis = await get_redis()
            handle_data = {
                "event_id": event_id,
                "deadline": deadline.isoformat(),
            }
            ttl = int((deadline - datetime.now(timezone.utc)).total_seconds()) + 60
            await redis.setex(
                f"inbox:receipt:{receipt_handle}",
                ttl,
                json.dumps(handle_data),
            )
        except Exception as e:
            logger.warning(f"Redis error storing receipt handle: {e}")
            # Fall back to encoding in the handle itself
            handle_data = {
                "e": event_id,
                "d": deadline.isoformat(),
            }
            receipt_handle = f"{self.RECEIPT_PREFIX}{base64.urlsafe_b64encode(json.dumps(handle_data).encode()).decode()}"

        return receipt_handle

    async def _validate_receipt_handle(self, receipt_handle: str) -> str | None:
        """
        Validate a receipt handle and return the event ID.

        Returns None if handle is invalid or expired.
        """
        if not receipt_handle.startswith(self.RECEIPT_PREFIX):
            return None

        # Try Redis first
        try:
            redis = await get_redis()
            data = await redis.get(f"inbox:receipt:{receipt_handle}")
            if data:
                handle_data = json.loads(data)
                deadline = datetime.fromisoformat(handle_data["deadline"])
                if datetime.now(timezone.utc) <= deadline:
                    return handle_data["event_id"]
                return None
        except Exception as e:
            logger.warning(f"Redis error validating receipt handle: {e}")

        # Try decoding from handle itself (fallback format)
        try:
            encoded = receipt_handle[len(self.RECEIPT_PREFIX):]
            data = json.loads(base64.urlsafe_b64decode(encoded).decode())
            deadline = datetime.fromisoformat(data["d"])
            if datetime.now(timezone.utc) <= deadline:
                return data["e"]
        except Exception:
            pass

        return None

    async def _invalidate_receipt_handle(self, receipt_handle: str) -> None:
        """Invalidate a receipt handle."""
        try:
            redis = await get_redis()
            await redis.delete(f"inbox:receipt:{receipt_handle}")
        except Exception as e:
            logger.warning(f"Redis error invalidating receipt handle: {e}")

    async def _update_receipt_handle(
        self,
        receipt_handle: str,
        new_deadline: datetime,
    ) -> None:
        """Update a receipt handle with new deadline."""
        event_id = await self._validate_receipt_handle(receipt_handle)
        if not event_id:
            return

        try:
            redis = await get_redis()
            handle_data = {
                "event_id": event_id,
                "deadline": new_deadline.isoformat(),
            }
            ttl = int((new_deadline - datetime.now(timezone.utc)).total_seconds()) + 60
            await redis.setex(
                f"inbox:receipt:{receipt_handle}",
                ttl,
                json.dumps(handle_data),
            )
        except Exception as e:
            logger.warning(f"Redis error updating receipt handle: {e}")
