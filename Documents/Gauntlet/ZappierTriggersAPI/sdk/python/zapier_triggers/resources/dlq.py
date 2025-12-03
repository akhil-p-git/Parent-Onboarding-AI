"""
DLQ (Dead Letter Queue) Resource.

Methods for interacting with the Dead Letter Queue API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, AsyncIterator

from zapier_triggers.models.dlq import (
    DLQItem,
    DLQStats,
    RetryResult,
    BatchRetryResult,
    DismissResult,
)
from zapier_triggers.models.common import PaginatedResponse, PaginationMeta

if TYPE_CHECKING:
    from zapier_triggers.client import TriggersClient


class DLQResource:
    """
    Resource for Dead Letter Queue operations.

    The DLQ contains events that failed delivery after exhausting
    all retry attempts.

    Example:
        ```python
        async with TriggersClient(api_key="...") as client:
            # List DLQ items
            items = await client.dlq.list()

            for item in items:
                print(f"Failed event: {item.event_id}")
                print(f"Reason: {item.failure_reason}")

                # Retry or dismiss
                if should_retry(item):
                    await client.dlq.retry(item.event_id)
                else:
                    await client.dlq.dismiss(item.event_id)
        ```
    """

    def __init__(self, client: TriggersClient) -> None:
        """Initialize the DLQ resource."""
        self._client = client

    async def list(
        self,
        event_type: str | None = None,
        source: str | None = None,
        subscription_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> PaginatedResponse[DLQItem]:
        """
        List items in the Dead Letter Queue.

        Args:
            event_type: Filter by event type
            source: Filter by source
            subscription_id: Filter by subscription
            limit: Maximum items to return (1-100)
            offset: Number of items to skip

        Returns:
            Paginated list of DLQ items

        Example:
            ```python
            items = await client.dlq.list(
                event_type="order.completed",
                limit=20,
            )

            for item in items:
                print(f"Event: {item.event_id}")
                print(f"Failed: {item.failure_reason}")
                print(f"Retries: {item.retry_count}")
            ```
        """
        params: dict[str, Any] = {
            "limit": limit,
            "offset": offset,
        }

        if event_type:
            params["event_type"] = event_type
        if source:
            params["source"] = source
        if subscription_id:
            params["subscription_id"] = subscription_id

        response = await self._client.request(
            "GET",
            "/api/v1/dlq",
            params=params,
        )
        data = response.json()

        items = [DLQItem.model_validate(item) for item in data.get("data", [])]

        pagination_data = data.get("pagination", {})
        pagination = PaginationMeta(
            limit=limit,
            has_more=offset + len(items) < pagination_data.get("total", len(items)),
            total=pagination_data.get("total"),
        )

        return PaginatedResponse[DLQItem](data=items, pagination=pagination)

    async def get(self, event_id: str) -> DLQItem:
        """
        Get a specific DLQ item by event ID.

        Args:
            event_id: The event ID

        Returns:
            The DLQ item

        Raises:
            NotFoundError: If the item doesn't exist in DLQ

        Example:
            ```python
            item = await client.dlq.get("evt_123")
            print(f"Failure reason: {item.failure_reason}")
            ```
        """
        response = await self._client.request(
            "GET",
            f"/api/v1/dlq/{event_id}",
        )
        return DLQItem.model_validate(response.json())

    async def stats(self) -> DLQStats:
        """
        Get DLQ statistics.

        Returns:
            DLQStats with counts and breakdowns

        Example:
            ```python
            stats = await client.dlq.stats()
            print(f"Total items: {stats.total_items}")
            print(f"By type: {stats.by_event_type}")
            ```
        """
        response = await self._client.request(
            "GET",
            "/api/v1/dlq/stats",
        )
        return DLQStats.model_validate(response.json())

    async def retry(
        self,
        event_id: str,
        modify_payload: dict[str, Any] | None = None,
    ) -> RetryResult:
        """
        Retry a failed event from the DLQ.

        The event will be re-queued for delivery.

        Args:
            event_id: The event ID to retry
            modify_payload: Optional payload modifications

        Returns:
            RetryResult indicating success

        Raises:
            NotFoundError: If the event isn't in the DLQ

        Example:
            ```python
            result = await client.dlq.retry("evt_123")
            if result.success:
                print("Event re-queued for delivery")
            ```
        """
        payload: dict[str, Any] = {}
        if modify_payload is not None:
            payload["modify_payload"] = modify_payload

        response = await self._client.request(
            "POST",
            f"/api/v1/dlq/{event_id}/retry",
            json=payload if payload else None,
        )
        return RetryResult.model_validate(response.json())

    async def batch_retry(
        self,
        event_ids: list[str],
    ) -> BatchRetryResult:
        """
        Retry multiple events from the DLQ.

        Args:
            event_ids: List of event IDs to retry

        Returns:
            BatchRetryResult with per-item results

        Example:
            ```python
            result = await client.dlq.batch_retry([
                "evt_123",
                "evt_456",
            ])
            print(f"Retried: {result.successful}, Failed: {result.failed}")
            ```
        """
        response = await self._client.request(
            "POST",
            "/api/v1/dlq/retry/batch",
            json={"event_ids": event_ids},
        )
        return BatchRetryResult.model_validate(response.json())

    async def dismiss(self, event_id: str) -> DismissResult:
        """
        Dismiss (remove) an event from the DLQ.

        The event will be permanently removed without retry.

        Args:
            event_id: The event ID to dismiss

        Returns:
            DismissResult indicating success

        Raises:
            NotFoundError: If the event isn't in the DLQ

        Example:
            ```python
            result = await client.dlq.dismiss("evt_123")
            if result.success:
                print("Event dismissed from DLQ")
            ```
        """
        response = await self._client.request(
            "DELETE",
            f"/api/v1/dlq/{event_id}",
        )
        return DismissResult.model_validate(response.json())

    async def batch_dismiss(
        self,
        event_ids: list[str],
    ) -> dict[str, Any]:
        """
        Dismiss multiple events from the DLQ.

        Args:
            event_ids: List of event IDs to dismiss

        Returns:
            Result with success/failure counts

        Example:
            ```python
            result = await client.dlq.batch_dismiss([
                "evt_123",
                "evt_456",
            ])
            print(f"Dismissed: {result['successful']}")
            ```
        """
        response = await self._client.request(
            "POST",
            "/api/v1/dlq/dismiss/batch",
            json={"event_ids": event_ids},
        )
        return response.json()

    async def purge(self, confirm: bool = False) -> dict[str, Any]:
        """
        Purge all items from the DLQ.

        WARNING: This permanently removes all DLQ items.

        Args:
            confirm: Must be True to confirm the purge

        Returns:
            Result with count of purged items

        Raises:
            ValidationError: If confirm is not True

        Example:
            ```python
            result = await client.dlq.purge(confirm=True)
            print(f"Purged {result['purged']} items")
            ```
        """
        response = await self._client.request(
            "DELETE",
            "/api/v1/dlq",
            params={"confirm": confirm},
        )
        return response.json()

    async def iterate(
        self,
        event_type: str | None = None,
        source: str | None = None,
        batch_size: int = 50,
    ) -> AsyncIterator[DLQItem]:
        """
        Iterate over all DLQ items.

        This method handles pagination automatically.

        Args:
            event_type: Filter by event type
            source: Filter by source
            batch_size: Number of items per page

        Yields:
            DLQItem objects

        Example:
            ```python
            async for item in client.dlq.iterate(event_type="order.*"):
                print(f"Failed: {item.event_id} - {item.failure_reason}")
            ```
        """
        offset = 0

        while True:
            page = await self.list(
                event_type=event_type,
                source=source,
                limit=batch_size,
                offset=offset,
            )

            for item in page.data:
                yield item

            if not page.pagination.has_more:
                break

            offset += len(page.data)
