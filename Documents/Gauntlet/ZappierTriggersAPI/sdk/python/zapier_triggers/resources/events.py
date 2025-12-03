"""
Events Resource.

Methods for interacting with the Events API.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any, AsyncIterator

from zapier_triggers.models.event import (
    Event,
    EventStatus,
    BatchEventResult,
    ReplayEventResponse,
)
from zapier_triggers.models.common import PaginatedResponse, PaginationMeta

if TYPE_CHECKING:
    from zapier_triggers.client import TriggersClient


class EventsResource:
    """
    Resource for event operations.

    Provides methods to create, retrieve, list, and replay events.

    Example:
        ```python
        async with TriggersClient(api_key="...") as client:
            # Create an event
            event = await client.events.create(
                event_type="user.created",
                source="my-service",
                data={"user_id": "123"},
            )

            # Get an event
            event = await client.events.get("evt_abc123")

            # List events
            events = await client.events.list(event_type="user.created")
        ```
    """

    def __init__(self, client: TriggersClient) -> None:
        """Initialize the events resource."""
        self._client = client

    async def create(
        self,
        event_type: str,
        source: str,
        data: dict[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> Event:
        """
        Create a new event.

        Args:
            event_type: Type of the event (e.g., "user.created")
            source: Source system creating the event
            data: Event payload data
            metadata: Optional metadata
            idempotency_key: Optional key for idempotent creation

        Returns:
            The created Event

        Raises:
            ValidationError: If the request is invalid
            ConflictError: If idempotency_key was already used

        Example:
            ```python
            event = await client.events.create(
                event_type="order.completed",
                source="orders-service",
                data={
                    "order_id": "ord_123",
                    "total": 99.99,
                    "customer_id": "cust_456",
                },
                idempotency_key="order-ord_123-completed",
            )
            print(f"Created: {event.id}")
            ```
        """
        payload: dict[str, Any] = {
            "event_type": event_type,
            "source": source,
            "data": data or {},
        }
        if metadata is not None:
            payload["metadata"] = metadata
        if idempotency_key is not None:
            payload["idempotency_key"] = idempotency_key

        response = await self._client.request(
            "POST",
            "/api/v1/events",
            json=payload,
        )
        return Event.model_validate(response.json())

    async def batch_create(
        self,
        events: list[dict[str, Any]],
        fail_fast: bool = False,
    ) -> BatchEventResult:
        """
        Create multiple events in a batch.

        Args:
            events: List of event dictionaries, each containing:
                - event_type: str
                - source: str
                - data: dict (optional)
                - metadata: dict (optional)
                - idempotency_key: str (optional)
                - reference_id: str (optional, for tracking)
            fail_fast: If True, stop on first error

        Returns:
            BatchEventResult with per-item results

        Example:
            ```python
            result = await client.events.batch_create([
                {"event_type": "user.created", "source": "auth", "data": {"id": "1"}},
                {"event_type": "user.created", "source": "auth", "data": {"id": "2"}},
            ])
            print(f"Created: {result.successful}, Failed: {result.failed}")
            ```
        """
        response = await self._client.request(
            "POST",
            "/api/v1/events/batch",
            json={"events": events, "fail_fast": fail_fast},
        )
        return BatchEventResult.model_validate(response.json())

    async def get(self, event_id: str) -> Event:
        """
        Get an event by ID.

        Args:
            event_id: The event ID (e.g., "evt_abc123")

        Returns:
            The Event

        Raises:
            NotFoundError: If the event doesn't exist

        Example:
            ```python
            event = await client.events.get("evt_abc123")
            print(f"Event type: {event.event_type}")
            print(f"Status: {event.status}")
            ```
        """
        response = await self._client.request(
            "GET",
            f"/api/v1/events/{event_id}",
        )
        return Event.model_validate(response.json())

    async def list(
        self,
        event_type: str | None = None,
        source: str | None = None,
        status: EventStatus | str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 100,
        cursor: str | None = None,
    ) -> PaginatedResponse[Event]:
        """
        List events with optional filters.

        Args:
            event_type: Filter by event type
            source: Filter by source
            status: Filter by status
            since: Filter events created after this time
            until: Filter events created before this time
            limit: Maximum number of events to return (1-1000)
            cursor: Pagination cursor from a previous response

        Returns:
            Paginated list of events

        Example:
            ```python
            # Get recent user events
            events = await client.events.list(
                event_type="user.created",
                limit=50,
            )

            for event in events:
                print(f"{event.id}: {event.event_type}")

            # Get next page
            if events.pagination.has_more:
                next_page = await client.events.list(
                    event_type="user.created",
                    cursor=events.pagination.next_cursor,
                )
            ```
        """
        params: dict[str, Any] = {"limit": limit}

        if event_type:
            params["event_type"] = event_type
        if source:
            params["source"] = source
        if status:
            params["status"] = status.value if isinstance(status, EventStatus) else status
        if since:
            params["since"] = since.isoformat()
        if until:
            params["until"] = until.isoformat()
        if cursor:
            params["cursor"] = cursor

        response = await self._client.request(
            "GET",
            "/api/v1/events",
            params=params,
        )
        data = response.json()

        return PaginatedResponse[Event](
            data=[Event.model_validate(e) for e in data["data"]],
            pagination=PaginationMeta.model_validate(data["pagination"]),
        )

    async def iterate(
        self,
        event_type: str | None = None,
        source: str | None = None,
        status: EventStatus | str | None = None,
        since: datetime | None = None,
        until: datetime | None = None,
        limit: int = 100,
    ) -> AsyncIterator[Event]:
        """
        Iterate over all events matching the filters.

        This method handles pagination automatically, yielding
        events one at a time.

        Args:
            event_type: Filter by event type
            source: Filter by source
            status: Filter by status
            since: Filter events created after this time
            until: Filter events created before this time
            limit: Page size for API requests

        Yields:
            Event objects

        Example:
            ```python
            async for event in client.events.iterate(
                event_type="user.created",
                since=datetime(2024, 1, 1),
            ):
                print(f"Processing: {event.id}")
            ```
        """
        cursor: str | None = None

        while True:
            page = await self.list(
                event_type=event_type,
                source=source,
                status=status,
                since=since,
                until=until,
                limit=limit,
                cursor=cursor,
            )

            for event in page.data:
                yield event

            if not page.pagination.has_more:
                break

            cursor = page.pagination.next_cursor

    async def get_deliveries(self, event_id: str) -> dict[str, Any]:
        """
        Get delivery attempts for an event.

        Args:
            event_id: The event ID

        Returns:
            Dictionary with delivery information

        Example:
            ```python
            deliveries = await client.events.get_deliveries("evt_123")
            for d in deliveries["deliveries"]:
                print(f"Subscription: {d['subscription_id']}, Status: {d['status']}")
            ```
        """
        response = await self._client.request(
            "GET",
            f"/api/v1/events/{event_id}/deliveries",
        )
        return response.json()

    async def replay(
        self,
        event_id: str,
        dry_run: bool = False,
        target_subscription_ids: list[str] | None = None,
        payload_override: dict[str, Any] | None = None,
        metadata_override: dict[str, Any] | None = None,
    ) -> ReplayEventResponse:
        """
        Replay an event.

        Re-sends an event to matching subscriptions, optionally with
        modifications.

        Args:
            event_id: The event ID to replay
            dry_run: If True, preview without executing
            target_subscription_ids: Specific subscriptions to target
            payload_override: Override event data
            metadata_override: Override event metadata

        Returns:
            ReplayEventResponse with results

        Example:
            ```python
            # Preview a replay
            preview = await client.events.replay(
                "evt_123",
                dry_run=True,
            )
            print(f"Would replay to: {preview.target_subscriptions}")

            # Execute replay
            result = await client.events.replay("evt_123")
            print(f"New event: {result.replay_event_id}")
            ```
        """
        payload: dict[str, Any] = {"dry_run": dry_run}
        if target_subscription_ids is not None:
            payload["target_subscription_ids"] = target_subscription_ids
        if payload_override is not None:
            payload["payload_override"] = payload_override
        if metadata_override is not None:
            payload["metadata_override"] = metadata_override

        response = await self._client.request(
            "POST",
            f"/api/v1/events/{event_id}/replay",
            json=payload,
        )
        return ReplayEventResponse.model_validate(response.json())
