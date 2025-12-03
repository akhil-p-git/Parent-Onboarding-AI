"""
Dead Letter Queue Service.

Handles DLQ inspection, retry, and management operations.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import get_redis
from app.core.utils import generate_prefixed_id
from app.models import Event, EventStatus
from app.services.queue_service import QueueService

logger = logging.getLogger(__name__)


class DLQError(Exception):
    """Base exception for DLQ errors."""

    def __init__(self, message: str, code: str = "dlq_error"):
        self.message = message
        self.code = code
        super().__init__(message)


class DLQItemNotFoundError(DLQError):
    """Raised when a DLQ item is not found."""

    def __init__(self, item_id: str):
        super().__init__(
            message=f"DLQ item with ID '{item_id}' not found",
            code="dlq_item_not_found",
        )


class DLQItem:
    """Represents an item in the dead letter queue."""

    def __init__(
        self,
        dlq_id: str,
        event_id: str,
        event_type: str,
        source: str,
        created_at: datetime | None,
        enqueued_at: datetime | None,
        dlq_entered_at: datetime | None = None,
        failure_reason: str | None = None,
        retry_count: int = 0,
        raw_message: str | None = None,
    ):
        self.dlq_id = dlq_id
        self.event_id = event_id
        self.event_type = event_type
        self.source = source
        self.created_at = created_at
        self.enqueued_at = enqueued_at
        self.dlq_entered_at = dlq_entered_at or datetime.now(timezone.utc)
        self.failure_reason = failure_reason
        self.retry_count = retry_count
        self.raw_message = raw_message

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary."""
        return {
            "dlq_id": self.dlq_id,
            "event_id": self.event_id,
            "event_type": self.event_type,
            "source": self.source,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "enqueued_at": self.enqueued_at.isoformat() if self.enqueued_at else None,
            "dlq_entered_at": self.dlq_entered_at.isoformat() if self.dlq_entered_at else None,
            "failure_reason": self.failure_reason,
            "retry_count": self.retry_count,
        }

    @classmethod
    def from_message(cls, message: dict[str, Any], index: int, raw: str) -> "DLQItem":
        """Create DLQItem from a queue message."""
        # Generate a DLQ ID based on the index for identification
        dlq_id = f"dlq_{message.get('event_id', 'unknown')}_{index}"

        created_at = None
        if message.get("created_at"):
            try:
                created_at = datetime.fromisoformat(message["created_at"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        enqueued_at = None
        if message.get("enqueued_at"):
            try:
                enqueued_at = datetime.fromisoformat(message["enqueued_at"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        dlq_entered_at = None
        if message.get("dlq_entered_at"):
            try:
                dlq_entered_at = datetime.fromisoformat(message["dlq_entered_at"].replace("Z", "+00:00"))
            except (ValueError, AttributeError):
                pass

        return cls(
            dlq_id=dlq_id,
            event_id=message.get("event_id", "unknown"),
            event_type=message.get("event_type", "unknown"),
            source=message.get("source", "unknown"),
            created_at=created_at,
            enqueued_at=enqueued_at,
            dlq_entered_at=dlq_entered_at,
            failure_reason=message.get("failure_reason"),
            retry_count=message.get("retry_count", 0),
            raw_message=raw,
        )


class DLQService:
    """Service for dead letter queue operations."""

    # Redis DLQ key (same as QueueService)
    EVENTS_DLQ = "queue:events:dlq"
    EVENTS_QUEUE = "queue:events"

    def __init__(self, db: AsyncSession | None = None):
        """Initialize with optional database session."""
        self.db = db
        self.queue_service = QueueService()

    async def list_items(
        self,
        limit: int = 100,
        offset: int = 0,
        event_type: str | None = None,
        source: str | None = None,
    ) -> tuple[list[DLQItem], int]:
        """
        List items in the dead letter queue.

        Args:
            limit: Maximum items to return
            offset: Number of items to skip
            event_type: Filter by event type
            source: Filter by source

        Returns:
            tuple: (list of DLQ items, total count)
        """
        try:
            redis = await get_redis()

            # Get total count
            total = await redis.llen(self.EVENTS_DLQ)

            if total == 0:
                return [], 0

            # Get all items (we need to filter in memory for Redis)
            # For large DLQs, consider using sorted sets or separate indexes
            all_items = await redis.lrange(self.EVENTS_DLQ, 0, -1)

            items = []
            for index, raw in enumerate(all_items):
                try:
                    message = json.loads(raw)
                    item = DLQItem.from_message(message, index, raw)

                    # Apply filters
                    if event_type and item.event_type != event_type:
                        continue
                    if source and item.source != source:
                        continue

                    items.append(item)
                except json.JSONDecodeError:
                    logger.warning(f"Invalid JSON in DLQ at index {index}")
                    continue

            # Get filtered total
            filtered_total = len(items)

            # Apply pagination
            paginated_items = items[offset : offset + limit]

            return paginated_items, filtered_total

        except Exception as e:
            logger.error(f"Error listing DLQ items: {e}")
            return [], 0

    async def get_item(self, event_id: str) -> DLQItem | None:
        """
        Get a specific item from the DLQ by event ID.

        Args:
            event_id: The event ID to find

        Returns:
            DLQItem | None: The DLQ item if found
        """
        try:
            redis = await get_redis()
            all_items = await redis.lrange(self.EVENTS_DLQ, 0, -1)

            for index, raw in enumerate(all_items):
                try:
                    message = json.loads(raw)
                    if message.get("event_id") == event_id:
                        return DLQItem.from_message(message, index, raw)
                except json.JSONDecodeError:
                    continue

            return None

        except Exception as e:
            logger.error(f"Error getting DLQ item: {e}")
            return None

    async def retry_item(
        self,
        event_id: str,
        modify_payload: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """
        Retry a dead-lettered event by moving it back to the main queue.

        Args:
            event_id: The event ID to retry
            modify_payload: Optional payload modifications

        Returns:
            dict: Result of the retry operation

        Raises:
            DLQItemNotFoundError: If the item is not found
        """
        try:
            redis = await get_redis()

            # Find and remove the item from DLQ
            all_items = await redis.lrange(self.EVENTS_DLQ, 0, -1)
            found_item = None
            found_raw = None

            for raw in all_items:
                try:
                    message = json.loads(raw)
                    if message.get("event_id") == event_id:
                        found_item = message
                        found_raw = raw
                        break
                except json.JSONDecodeError:
                    continue

            if not found_item:
                raise DLQItemNotFoundError(event_id)

            # Remove from DLQ
            removed = await redis.lrem(self.EVENTS_DLQ, 1, found_raw)
            if removed == 0:
                raise DLQItemNotFoundError(event_id)

            # Prepare the message for retry
            retry_message = dict(found_item)
            retry_message["retry_count"] = retry_message.get("retry_count", 0) + 1
            retry_message["retried_at"] = datetime.now(timezone.utc).isoformat()

            # Apply payload modifications if any
            if modify_payload:
                retry_message.update(modify_payload)

            # Re-enqueue to main queue
            await redis.lpush(self.EVENTS_QUEUE, json.dumps(retry_message))

            logger.info(f"Retried DLQ item for event {event_id}")

            # Update event status in database if we have a session
            if self.db:
                await self._update_event_status(event_id, EventStatus.PENDING)

            return {
                "success": True,
                "event_id": event_id,
                "message": "Event re-queued for processing",
                "retry_count": retry_message["retry_count"],
            }

        except DLQItemNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error retrying DLQ item: {e}")
            raise DLQError(f"Failed to retry item: {str(e)}")

    async def retry_batch(
        self,
        event_ids: list[str],
    ) -> dict[str, Any]:
        """
        Retry multiple dead-lettered events.

        Args:
            event_ids: List of event IDs to retry

        Returns:
            dict: Results of the batch retry operation
        """
        results = {
            "total": len(event_ids),
            "successful": 0,
            "failed": 0,
            "results": [],
        }

        for event_id in event_ids:
            try:
                result = await self.retry_item(event_id)
                results["successful"] += 1
                results["results"].append({
                    "event_id": event_id,
                    "success": True,
                })
            except DLQItemNotFoundError:
                results["failed"] += 1
                results["results"].append({
                    "event_id": event_id,
                    "success": False,
                    "error": "Item not found in DLQ",
                })
            except Exception as e:
                results["failed"] += 1
                results["results"].append({
                    "event_id": event_id,
                    "success": False,
                    "error": str(e),
                })

        return results

    async def dismiss_item(self, event_id: str) -> dict[str, Any]:
        """
        Permanently dismiss an item from the DLQ.

        Args:
            event_id: The event ID to dismiss

        Returns:
            dict: Result of the dismiss operation

        Raises:
            DLQItemNotFoundError: If the item is not found
        """
        try:
            redis = await get_redis()

            # Find and remove the item from DLQ
            all_items = await redis.lrange(self.EVENTS_DLQ, 0, -1)
            found_raw = None

            for raw in all_items:
                try:
                    message = json.loads(raw)
                    if message.get("event_id") == event_id:
                        found_raw = raw
                        break
                except json.JSONDecodeError:
                    continue

            if not found_raw:
                raise DLQItemNotFoundError(event_id)

            # Remove from DLQ
            removed = await redis.lrem(self.EVENTS_DLQ, 1, found_raw)
            if removed == 0:
                raise DLQItemNotFoundError(event_id)

            logger.info(f"Dismissed DLQ item for event {event_id}")

            # Update event status in database if we have a session
            if self.db:
                await self._update_event_status(event_id, EventStatus.FAILED)

            return {
                "success": True,
                "event_id": event_id,
                "message": "Event permanently dismissed from DLQ",
            }

        except DLQItemNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error dismissing DLQ item: {e}")
            raise DLQError(f"Failed to dismiss item: {str(e)}")

    async def dismiss_batch(
        self,
        event_ids: list[str],
    ) -> dict[str, Any]:
        """
        Dismiss multiple items from the DLQ.

        Args:
            event_ids: List of event IDs to dismiss

        Returns:
            dict: Results of the batch dismiss operation
        """
        results = {
            "total": len(event_ids),
            "successful": 0,
            "failed": 0,
            "results": [],
        }

        for event_id in event_ids:
            try:
                result = await self.dismiss_item(event_id)
                results["successful"] += 1
                results["results"].append({
                    "event_id": event_id,
                    "success": True,
                })
            except DLQItemNotFoundError:
                results["failed"] += 1
                results["results"].append({
                    "event_id": event_id,
                    "success": False,
                    "error": "Item not found in DLQ",
                })
            except Exception as e:
                results["failed"] += 1
                results["results"].append({
                    "event_id": event_id,
                    "success": False,
                    "error": str(e),
                })

        return results

    async def purge(self) -> dict[str, Any]:
        """
        Purge all items from the DLQ.

        Returns:
            dict: Result of the purge operation
        """
        try:
            redis = await get_redis()

            # Get count before purging
            count = await redis.llen(self.EVENTS_DLQ)

            # Delete the DLQ
            await redis.delete(self.EVENTS_DLQ)

            logger.warning(f"Purged {count} items from DLQ")

            return {
                "success": True,
                "purged_count": count,
                "message": f"Purged {count} items from the dead letter queue",
            }

        except Exception as e:
            logger.error(f"Error purging DLQ: {e}")
            raise DLQError(f"Failed to purge DLQ: {str(e)}")

    async def get_stats(self) -> dict[str, Any]:
        """
        Get DLQ statistics.

        Returns:
            dict: DLQ statistics
        """
        try:
            redis = await get_redis()

            total = await redis.llen(self.EVENTS_DLQ)

            # Get breakdown by event type and source
            by_type: dict[str, int] = {}
            by_source: dict[str, int] = {}
            oldest_item = None
            newest_item = None

            if total > 0:
                all_items = await redis.lrange(self.EVENTS_DLQ, 0, -1)

                for raw in all_items:
                    try:
                        message = json.loads(raw)
                        event_type = message.get("event_type", "unknown")
                        source = message.get("source", "unknown")

                        by_type[event_type] = by_type.get(event_type, 0) + 1
                        by_source[source] = by_source.get(source, 0) + 1

                        # Track oldest and newest
                        enqueued_at = message.get("enqueued_at")
                        if enqueued_at:
                            if oldest_item is None or enqueued_at < oldest_item:
                                oldest_item = enqueued_at
                            if newest_item is None or enqueued_at > newest_item:
                                newest_item = enqueued_at

                    except json.JSONDecodeError:
                        continue

            return {
                "total": total,
                "by_event_type": by_type,
                "by_source": by_source,
                "oldest_item": oldest_item,
                "newest_item": newest_item,
            }

        except Exception as e:
            logger.error(f"Error getting DLQ stats: {e}")
            return {"total": 0, "by_event_type": {}, "by_source": {}}

    async def _update_event_status(
        self,
        event_id: str,
        status: EventStatus,
    ) -> None:
        """Update event status in the database."""
        if not self.db:
            return

        try:
            result = await self.db.execute(
                select(Event).where(Event.id == event_id)
            )
            event = result.scalar_one_or_none()
            if event:
                event.status = status
                await self.db.flush()
        except Exception as e:
            logger.warning(f"Failed to update event status: {e}")
