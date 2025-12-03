"""
Queue Service.

Handles event queuing for async processing using Redis or SQS.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.core.redis import get_redis
from app.models import Event

logger = logging.getLogger(__name__)


class QueueService:
    """Service for event queue operations."""

    # Redis queue keys
    EVENTS_QUEUE = "queue:events"
    EVENTS_PROCESSING = "queue:events:processing"
    EVENTS_DLQ = "queue:events:dlq"

    # Message visibility timeout (seconds)
    VISIBILITY_TIMEOUT = 30

    async def enqueue_event(self, event: Event) -> None:
        """
        Enqueue an event for processing.

        Uses Redis as the primary queue, with fallback to SQS if configured.

        Args:
            event: The event to enqueue
        """
        message = self._build_message(event)

        # Try SQS first if configured
        if settings.SQS_EVENTS_QUEUE_URL:
            await self._enqueue_sqs(message)
        else:
            await self._enqueue_redis(message)

    async def enqueue_events_batch(self, events: list[Event]) -> None:
        """
        Enqueue multiple events.

        Args:
            events: List of events to enqueue
        """
        messages = [self._build_message(event) for event in events]

        if settings.SQS_EVENTS_QUEUE_URL:
            await self._enqueue_sqs_batch(messages)
        else:
            await self._enqueue_redis_batch(messages)

    async def dequeue_events(
        self,
        count: int = 10,
        visibility_timeout: int | None = None,
    ) -> list[dict[str, Any]]:
        """
        Dequeue events for processing.

        Args:
            count: Maximum number of events to dequeue
            visibility_timeout: Seconds before events become visible again

        Returns:
            list: List of event messages with receipt handles
        """
        timeout = visibility_timeout or self.VISIBILITY_TIMEOUT

        if settings.SQS_EVENTS_QUEUE_URL:
            return await self._dequeue_sqs(count, timeout)
        else:
            return await self._dequeue_redis(count, timeout)

    async def acknowledge_event(self, receipt_handle: str) -> bool:
        """
        Acknowledge successful processing of an event.

        Args:
            receipt_handle: Receipt handle from dequeue operation

        Returns:
            bool: Whether acknowledgment was successful
        """
        if settings.SQS_EVENTS_QUEUE_URL:
            return await self._ack_sqs(receipt_handle)
        else:
            return await self._ack_redis(receipt_handle)

    async def nack_event(self, receipt_handle: str, requeue: bool = True) -> bool:
        """
        Negative acknowledge - return event to queue or send to DLQ.

        Args:
            receipt_handle: Receipt handle from dequeue operation
            requeue: Whether to requeue (True) or send to DLQ (False)

        Returns:
            bool: Whether operation was successful
        """
        if settings.SQS_EVENTS_QUEUE_URL:
            return await self._nack_sqs(receipt_handle, requeue)
        else:
            return await self._nack_redis(receipt_handle, requeue)

    async def get_queue_stats(self) -> dict[str, int]:
        """
        Get queue statistics.

        Returns:
            dict: Queue statistics (pending, processing, dlq counts)
        """
        if settings.SQS_EVENTS_QUEUE_URL:
            return await self._get_sqs_stats()
        else:
            return await self._get_redis_stats()

    def _build_message(self, event: Event) -> dict[str, Any]:
        """Build a queue message from an event."""
        return {
            "event_id": event.id,
            "event_type": event.event_type,
            "source": event.source,
            "created_at": event.created_at.isoformat() if event.created_at else None,
            "enqueued_at": datetime.now(timezone.utc).isoformat(),
        }

    # Redis queue implementation
    async def _enqueue_redis(self, message: dict[str, Any]) -> None:
        """Enqueue message to Redis."""
        try:
            redis = await get_redis()
            await redis.lpush(self.EVENTS_QUEUE, json.dumps(message))
            logger.debug(f"Enqueued event {message['event_id']} to Redis")
        except Exception as e:
            logger.error(f"Error enqueueing to Redis: {e}")
            raise

    async def _enqueue_redis_batch(self, messages: list[dict[str, Any]]) -> None:
        """Enqueue multiple messages to Redis."""
        try:
            redis = await get_redis()
            pipeline = redis.pipeline()
            for message in messages:
                pipeline.lpush(self.EVENTS_QUEUE, json.dumps(message))
            await pipeline.execute()
            logger.debug(f"Enqueued {len(messages)} events to Redis")
        except Exception as e:
            logger.error(f"Error batch enqueueing to Redis: {e}")
            raise

    async def _dequeue_redis(
        self,
        count: int,
        visibility_timeout: int,
    ) -> list[dict[str, Any]]:
        """Dequeue messages from Redis with visibility timeout."""
        try:
            redis = await get_redis()
            messages = []

            for _ in range(count):
                # Move from queue to processing set atomically
                result = await redis.rpoplpush(
                    self.EVENTS_QUEUE,
                    self.EVENTS_PROCESSING,
                )
                if result is None:
                    break

                message = json.loads(result)
                receipt_handle = f"redis:{message['event_id']}:{datetime.now(timezone.utc).timestamp()}"

                # Store receipt handle mapping
                await redis.setex(
                    f"receipt:{receipt_handle}",
                    visibility_timeout,
                    result,
                )

                messages.append({
                    "message": message,
                    "receipt_handle": receipt_handle,
                })

            return messages

        except Exception as e:
            logger.error(f"Error dequeuing from Redis: {e}")
            return []

    async def _ack_redis(self, receipt_handle: str) -> bool:
        """Acknowledge message in Redis."""
        try:
            redis = await get_redis()

            # Get the original message
            message_json = await redis.get(f"receipt:{receipt_handle}")
            if not message_json:
                return False

            # Remove from processing and receipt mapping
            await redis.lrem(self.EVENTS_PROCESSING, 1, message_json)
            await redis.delete(f"receipt:{receipt_handle}")

            return True

        except Exception as e:
            logger.error(f"Error acknowledging in Redis: {e}")
            return False

    async def _nack_redis(self, receipt_handle: str, requeue: bool) -> bool:
        """Negative acknowledge message in Redis."""
        try:
            redis = await get_redis()

            # Get the original message
            message_json = await redis.get(f"receipt:{receipt_handle}")
            if not message_json:
                return False

            # Remove from processing
            await redis.lrem(self.EVENTS_PROCESSING, 1, message_json)
            await redis.delete(f"receipt:{receipt_handle}")

            if requeue:
                # Put back in queue
                await redis.lpush(self.EVENTS_QUEUE, message_json)
            else:
                # Send to DLQ
                await redis.lpush(self.EVENTS_DLQ, message_json)

            return True

        except Exception as e:
            logger.error(f"Error nacking in Redis: {e}")
            return False

    async def _get_redis_stats(self) -> dict[str, int]:
        """Get Redis queue statistics."""
        try:
            redis = await get_redis()
            return {
                "pending": await redis.llen(self.EVENTS_QUEUE),
                "processing": await redis.llen(self.EVENTS_PROCESSING),
                "dlq": await redis.llen(self.EVENTS_DLQ),
            }
        except Exception as e:
            logger.error(f"Error getting Redis stats: {e}")
            return {"pending": 0, "processing": 0, "dlq": 0}

    # SQS queue implementation (placeholder)
    async def _enqueue_sqs(self, message: dict[str, Any]) -> None:
        """Enqueue message to SQS."""
        # TODO: Implement SQS integration
        logger.warning("SQS not implemented, falling back to Redis")
        await self._enqueue_redis(message)

    async def _enqueue_sqs_batch(self, messages: list[dict[str, Any]]) -> None:
        """Enqueue multiple messages to SQS."""
        # TODO: Implement SQS batch integration
        logger.warning("SQS not implemented, falling back to Redis")
        await self._enqueue_redis_batch(messages)

    async def _dequeue_sqs(
        self,
        count: int,
        visibility_timeout: int,
    ) -> list[dict[str, Any]]:
        """Dequeue messages from SQS."""
        # TODO: Implement SQS integration
        logger.warning("SQS not implemented, falling back to Redis")
        return await self._dequeue_redis(count, visibility_timeout)

    async def _ack_sqs(self, receipt_handle: str) -> bool:
        """Acknowledge message in SQS."""
        # TODO: Implement SQS integration
        return await self._ack_redis(receipt_handle)

    async def _nack_sqs(self, receipt_handle: str, requeue: bool) -> bool:
        """Negative acknowledge message in SQS."""
        # TODO: Implement SQS integration
        return await self._nack_redis(receipt_handle, requeue)

    async def _get_sqs_stats(self) -> dict[str, int]:
        """Get SQS queue statistics."""
        # TODO: Implement SQS integration
        return await self._get_redis_stats()
