"""
Event Service.

Handles event creation, validation, and persistence.
"""

import json
import logging
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import RedisKeys, get_redis
from app.core.utils import generate_prefixed_id
from app.models import Event, EventStatus
from app.schemas import (
    BatchCreateEventRequest,
    BatchCreateEventResponse,
    BatchEventError,
    BatchEventResultItem,
    CreateEventRequest,
    EventResponse,
)
from app.services.streaming_service import publish_event_to_stream

logger = logging.getLogger(__name__)


class IdempotencyError(Exception):
    """Raised when an idempotency key conflict is detected."""

    def __init__(self, existing_event_id: str):
        self.existing_event_id = existing_event_id
        super().__init__(f"Idempotency key already used for event: {existing_event_id}")


class EventService:
    """Service for event operations."""

    # Idempotency key TTL (24 hours)
    IDEMPOTENCY_TTL = 86400

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db

    async def create_event(
        self,
        request: CreateEventRequest,
        api_key_id: str | None = None,
    ) -> Event:
        """
        Create a new event.

        Args:
            request: Event creation request
            api_key_id: ID of the API key creating the event

        Returns:
            Event: The created event

        Raises:
            IdempotencyError: If idempotency key already used
        """
        # Check idempotency key
        if request.idempotency_key:
            existing = await self._check_idempotency(request.idempotency_key)
            if existing:
                raise IdempotencyError(existing)

        # Generate event ID
        event_id = generate_prefixed_id("evt")

        # Create event record
        event = Event(
            id=event_id,
            event_type=request.event_type,
            source=request.source,
            data=request.data,
            event_meta=request.metadata,
            status=EventStatus.PENDING,
            idempotency_key=request.idempotency_key,
            api_key_id=api_key_id,
        )

        self.db.add(event)
        await self.db.flush()

        # Store idempotency key
        if request.idempotency_key:
            await self._store_idempotency(request.idempotency_key, event_id)

        # Enqueue for processing
        await self._enqueue_event(event)

        # Publish to SSE stream for real-time subscribers
        await publish_event_to_stream({
            "id": event.id,
            "event_type": event.event_type,
            "source": event.source,
            "data": event.data,
            "metadata": event.event_meta,
            "status": event.status.value,
            "created_at": event.created_at.isoformat() if event.created_at else None,
        })

        logger.info(
            f"Created event {event_id} of type {request.event_type} from {request.source}"
        )

        return event

    async def create_events_batch(
        self,
        request: BatchCreateEventRequest,
        api_key_id: str | None = None,
    ) -> BatchCreateEventResponse:
        """
        Create multiple events in a batch.

        Args:
            request: Batch event creation request
            api_key_id: ID of the API key creating the events

        Returns:
            BatchCreateEventResponse: Results for each event
        """
        results: list[BatchEventResultItem] = []
        successful = 0
        failed = 0

        for index, item in enumerate(request.events):
            try:
                # Check idempotency
                if item.idempotency_key:
                    existing = await self._check_idempotency(item.idempotency_key)
                    if existing:
                        raise IdempotencyError(existing)

                # Generate event ID
                event_id = generate_prefixed_id("evt")

                # Create event record
                event = Event(
                    id=event_id,
                    event_type=item.event_type,
                    source=item.source,
                    data=item.data,
                    event_meta=item.metadata,
                    status=EventStatus.PENDING,
                    idempotency_key=item.idempotency_key,
                    api_key_id=api_key_id,
                )

                self.db.add(event)
                await self.db.flush()

                # Store idempotency key
                if item.idempotency_key:
                    await self._store_idempotency(item.idempotency_key, event_id)

                # Enqueue for processing
                await self._enqueue_event(event)

                # Publish to SSE stream for real-time subscribers
                await publish_event_to_stream({
                    "id": event.id,
                    "event_type": event.event_type,
                    "source": event.source,
                    "data": event.data,
                    "metadata": event.event_meta,
                    "status": event.status.value,
                    "created_at": event.created_at.isoformat() if event.created_at else None,
                })

                # Build response
                event_response = EventResponse(
                    id=event.id,
                    event_type=event.event_type,
                    source=event.source,
                    data=event.data,
                    metadata=event.event_meta,
                    status=event.status,
                    idempotency_key=event.idempotency_key,
                    created_at=event.created_at,
                    updated_at=event.updated_at,
                    delivery_attempts=event.delivery_attempts,
                    successful_deliveries=event.successful_deliveries,
                    failed_deliveries=event.failed_deliveries,
                )

                results.append(
                    BatchEventResultItem(
                        index=index,
                        reference_id=item.reference_id,
                        success=True,
                        event=event_response,
                        error=None,
                    )
                )
                successful += 1

            except IdempotencyError as e:
                results.append(
                    BatchEventResultItem(
                        index=index,
                        reference_id=item.reference_id,
                        success=False,
                        event=None,
                        error=BatchEventError(
                            code="duplicate_idempotency_key",
                            message=f"Idempotency key already used for event: {e.existing_event_id}",
                            field="idempotency_key",
                        ),
                    )
                )
                failed += 1

                if request.fail_fast:
                    # Mark remaining as skipped
                    for remaining_index in range(index + 1, len(request.events)):
                        remaining_item = request.events[remaining_index]
                        results.append(
                            BatchEventResultItem(
                                index=remaining_index,
                                reference_id=remaining_item.reference_id,
                                success=False,
                                event=None,
                                error=BatchEventError(
                                    code="skipped",
                                    message="Skipped due to fail_fast mode",
                                ),
                            )
                        )
                        failed += 1
                    break

            except Exception as e:
                logger.error(f"Error creating event at index {index}: {e}")
                results.append(
                    BatchEventResultItem(
                        index=index,
                        reference_id=item.reference_id,
                        success=False,
                        event=None,
                        error=BatchEventError(
                            code="internal_error",
                            message=str(e),
                        ),
                    )
                )
                failed += 1

                if request.fail_fast:
                    # Mark remaining as skipped
                    for remaining_index in range(index + 1, len(request.events)):
                        remaining_item = request.events[remaining_index]
                        results.append(
                            BatchEventResultItem(
                                index=remaining_index,
                                reference_id=remaining_item.reference_id,
                                success=False,
                                event=None,
                                error=BatchEventError(
                                    code="skipped",
                                    message="Skipped due to fail_fast mode",
                                ),
                            )
                        )
                        failed += 1
                    break

        logger.info(
            f"Batch created: {successful} successful, {failed} failed out of {len(request.events)}"
        )

        return BatchCreateEventResponse(
            total=len(request.events),
            successful=successful,
            failed=failed,
            results=results,
        )

    async def get_event(self, event_id: str) -> Event | None:
        """
        Get an event by ID.

        Args:
            event_id: The event ID

        Returns:
            Event | None: The event if found
        """
        result = await self.db.execute(
            select(Event).where(Event.id == event_id)
        )
        return result.scalar_one_or_none()

    async def get_event_by_idempotency_key(self, key: str) -> Event | None:
        """
        Get an event by idempotency key.

        Args:
            key: The idempotency key

        Returns:
            Event | None: The event if found
        """
        result = await self.db.execute(
            select(Event).where(Event.idempotency_key == key)
        )
        return result.scalar_one_or_none()

    async def list_events(
        self,
        event_type: str | None = None,
        source: str | None = None,
        status: EventStatus | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 100,
        cursor: str | None = None,
    ) -> tuple[list[Event], str | None]:
        """
        List events with optional filters.

        Args:
            event_type: Filter by event type
            source: Filter by source
            status: Filter by status
            since: Filter events created after this time
            until: Filter events created before this time
            limit: Maximum events to return
            cursor: Pagination cursor

        Returns:
            tuple: (list of events, next cursor or None)
        """
        query = select(Event).order_by(Event.created_at.desc())

        if event_type:
            query = query.where(Event.event_type == event_type)
        if source:
            query = query.where(Event.source == source)
        if status:
            query = query.where(Event.status == status)
        if since:
            query = query.where(Event.created_at >= since)
        if until:
            query = query.where(Event.created_at <= until)

        # Handle cursor pagination
        if cursor:
            try:
                import base64
                cursor_data = json.loads(base64.b64decode(cursor).decode())
                cursor_id = cursor_data.get("id")
                if cursor_id:
                    query = query.where(Event.id < cursor_id)
            except Exception:
                pass  # Invalid cursor, ignore

        # Fetch one extra to determine if there are more
        query = query.limit(limit + 1)

        result = await self.db.execute(query)
        events = list(result.scalars().all())

        # Determine next cursor
        next_cursor = None
        if len(events) > limit:
            events = events[:limit]
            last_event = events[-1]
            import base64
            cursor_data = {"id": last_event.id}
            next_cursor = base64.b64encode(
                json.dumps(cursor_data).encode()
            ).decode()

        return events, next_cursor

    async def _check_idempotency(self, key: str) -> str | None:
        """
        Check if an idempotency key has been used.

        Returns:
            str | None: Existing event ID if key was used, None otherwise
        """
        try:
            redis = await get_redis()
            cache_key = RedisKeys.idempotency(key)
            existing_id = await redis.get(cache_key)
            return existing_id
        except Exception as e:
            logger.warning(f"Redis error checking idempotency: {e}")
            # Fall back to database check
            event = await self.get_event_by_idempotency_key(key)
            return event.id if event else None

    async def _store_idempotency(self, key: str, event_id: str) -> None:
        """
        Store an idempotency key.

        Args:
            key: The idempotency key
            event_id: The event ID it maps to
        """
        try:
            redis = await get_redis()
            cache_key = RedisKeys.idempotency(key)
            await redis.setex(cache_key, self.IDEMPOTENCY_TTL, event_id)
        except Exception as e:
            logger.warning(f"Redis error storing idempotency: {e}")

    async def _enqueue_event(self, event: Event) -> None:
        """
        Enqueue an event for processing.

        Args:
            event: The event to enqueue
        """
        from app.services.queue_service import QueueService

        try:
            queue_service = QueueService()
            await queue_service.enqueue_event(event)
        except Exception as e:
            logger.error(f"Error enqueueing event {event.id}: {e}")
            # Don't fail the event creation, just log the error
            # The event will be picked up by a background job
