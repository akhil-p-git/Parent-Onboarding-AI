"""
Inbox Resource.

Methods for interacting with the Inbox API.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, AsyncIterator

from zapier_triggers.models.inbox import (
    InboxItem,
    AcknowledgeResult,
    InboxStats,
)
from zapier_triggers.models.common import PaginatedResponse, PaginationMeta

if TYPE_CHECKING:
    from zapier_triggers.client import TriggersClient


class InboxResource:
    """
    Resource for inbox operations.

    The inbox contains events that have been delivered to a subscription
    and are waiting to be acknowledged.

    Example:
        ```python
        async with TriggersClient(api_key="...") as client:
            # List inbox items
            items = await client.inbox.list()

            # Process and acknowledge
            for item in items:
                process_event(item.data)
                await client.inbox.acknowledge([item.receipt_handle])
        ```
    """

    def __init__(self, client: TriggersClient) -> None:
        """Initialize the inbox resource."""
        self._client = client

    async def list(
        self,
        subscription_id: str | None = None,
        event_type: str | None = None,
        limit: int = 10,
        visibility_timeout: int | None = None,
    ) -> PaginatedResponse[InboxItem]:
        """
        List items in the inbox.

        Args:
            subscription_id: Filter by subscription
            event_type: Filter by event type
            limit: Maximum items to return (1-100)
            visibility_timeout: Seconds to hide items from other consumers

        Returns:
            Paginated list of inbox items

        Example:
            ```python
            items = await client.inbox.list(
                subscription_id="sub_123",
                limit=10,
            )

            for item in items:
                print(f"Event: {item.event_type}")
                print(f"Handle: {item.receipt_handle}")
            ```
        """
        params: dict[str, Any] = {"limit": limit}

        if subscription_id:
            params["subscription_id"] = subscription_id
        if event_type:
            params["event_type"] = event_type
        if visibility_timeout is not None:
            params["visibility_timeout"] = visibility_timeout

        response = await self._client.request(
            "GET",
            "/api/v1/inbox",
            params=params,
        )
        data = response.json()

        items = [InboxItem.model_validate(item) for item in data.get("data", [])]

        # Build pagination metadata
        pagination_data = data.get("pagination", {})
        pagination = PaginationMeta(
            limit=limit,
            has_more=pagination_data.get("has_more", False),
            next_cursor=pagination_data.get("next_cursor"),
            total=pagination_data.get("total"),
        )

        return PaginatedResponse[InboxItem](data=items, pagination=pagination)

    async def acknowledge(
        self,
        receipt_handles: list[str],
    ) -> AcknowledgeResult:
        """
        Acknowledge processed inbox items.

        Once acknowledged, items are removed from the inbox.

        Args:
            receipt_handles: List of receipt handles to acknowledge

        Returns:
            AcknowledgeResult with success/failure counts

        Example:
            ```python
            result = await client.inbox.acknowledge([
                "rh_abc123",
                "rh_def456",
            ])
            print(f"Acknowledged: {result.successful}")
            ```
        """
        response = await self._client.request(
            "POST",
            "/api/v1/inbox/ack",
            json={"receipt_handles": receipt_handles},
        )
        return AcknowledgeResult.model_validate(response.json())

    async def stats(
        self,
        subscription_id: str | None = None,
    ) -> InboxStats:
        """
        Get inbox statistics.

        Args:
            subscription_id: Filter stats by subscription

        Returns:
            InboxStats with counts and metrics

        Example:
            ```python
            stats = await client.inbox.stats(subscription_id="sub_123")
            print(f"Pending: {stats.pending_count}")
            ```
        """
        params: dict[str, Any] = {}
        if subscription_id:
            params["subscription_id"] = subscription_id

        response = await self._client.request(
            "GET",
            "/api/v1/inbox/stats",
            params=params,
        )
        return InboxStats.model_validate(response.json())

    async def iterate(
        self,
        subscription_id: str | None = None,
        event_type: str | None = None,
        batch_size: int = 10,
        visibility_timeout: int | None = None,
        auto_acknowledge: bool = False,
    ) -> AsyncIterator[InboxItem]:
        """
        Iterate over inbox items, optionally auto-acknowledging.

        This method polls the inbox continuously, yielding items
        as they become available.

        Args:
            subscription_id: Filter by subscription
            event_type: Filter by event type
            batch_size: Number of items to fetch per request
            visibility_timeout: Seconds to hide items from other consumers
            auto_acknowledge: Automatically acknowledge after yielding

        Yields:
            InboxItem objects

        Example:
            ```python
            # Process items with auto-acknowledge
            async for item in client.inbox.iterate(
                subscription_id="sub_123",
                auto_acknowledge=True,
            ):
                process_event(item.data)
                # Item is automatically acknowledged
            ```
        """
        while True:
            page = await self.list(
                subscription_id=subscription_id,
                event_type=event_type,
                limit=batch_size,
                visibility_timeout=visibility_timeout,
            )

            if not page.data:
                # No items available, stop iteration
                break

            for item in page.data:
                yield item

                if auto_acknowledge:
                    await self.acknowledge([item.receipt_handle])

    async def poll(
        self,
        subscription_id: str | None = None,
        event_type: str | None = None,
        batch_size: int = 10,
        visibility_timeout: int = 30,
        max_iterations: int | None = None,
        auto_acknowledge: bool = False,
    ) -> AsyncIterator[InboxItem]:
        """
        Continuously poll the inbox for new items.

        Unlike `iterate()`, this method continues polling even when
        the inbox is empty, making it suitable for long-running consumers.

        Args:
            subscription_id: Filter by subscription
            event_type: Filter by event type
            batch_size: Number of items to fetch per request
            visibility_timeout: Seconds to hide items from other consumers
            max_iterations: Maximum number of poll iterations (None = infinite)
            auto_acknowledge: Automatically acknowledge after yielding

        Yields:
            InboxItem objects

        Example:
            ```python
            # Long-running consumer
            async for item in client.inbox.poll(
                subscription_id="sub_123",
                auto_acknowledge=True,
            ):
                await process_event(item.data)
            ```
        """
        import asyncio

        iterations = 0

        while max_iterations is None or iterations < max_iterations:
            iterations += 1

            page = await self.list(
                subscription_id=subscription_id,
                event_type=event_type,
                limit=batch_size,
                visibility_timeout=visibility_timeout,
            )

            if not page.data:
                # No items, wait before polling again
                await asyncio.sleep(1)
                continue

            for item in page.data:
                yield item

                if auto_acknowledge:
                    await self.acknowledge([item.receipt_handle])
