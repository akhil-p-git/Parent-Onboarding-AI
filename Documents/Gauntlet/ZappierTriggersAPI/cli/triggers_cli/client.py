"""
Triggers API Client.

HTTP client for interacting with the Triggers API.
"""

import json
from typing import Any, AsyncIterator

import httpx
from httpx_sse import aconnect_sse

from triggers_cli.config import get_config


class ApiError(Exception):
    """API error with status code and details."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ):
        self.message = message
        self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class TriggersClient:
    """Client for the Triggers API."""

    def __init__(
        self,
        api_url: str | None = None,
        api_key: str | None = None,
        timeout: int | None = None,
    ):
        """Initialize the client."""
        config = get_config()
        self.api_url = (api_url or config.api_url).rstrip("/")
        self.api_key = api_key or config.api_key
        self.timeout = timeout or config.timeout

        if not self.api_url.endswith("/api/v1"):
            self.api_url = f"{self.api_url}/api/v1"

    def _get_headers(self) -> dict[str, str]:
        """Get request headers including authentication."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _handle_response(self, response: httpx.Response) -> dict[str, Any]:
        """Handle API response and raise errors if needed."""
        if response.status_code >= 400:
            try:
                error_data = response.json()
                detail = error_data.get("detail", {})
                if isinstance(detail, dict):
                    message = detail.get("detail", str(error_data))
                else:
                    message = str(detail)
            except Exception:
                message = response.text or f"HTTP {response.status_code}"

            raise ApiError(
                message=message,
                status_code=response.status_code,
                details=error_data if "error_data" in dir() else {},
            )

        if response.status_code == 204:
            return {}

        return response.json()

    # Events API

    async def send_event(
        self,
        event_type: str,
        source: str,
        data: dict[str, Any],
        metadata: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
    ) -> dict[str, Any]:
        """Send a single event to the API."""
        payload = {
            "event_type": event_type,
            "source": source,
            "data": data,
        }
        if metadata:
            payload["metadata"] = metadata
        if idempotency_key:
            payload["idempotency_key"] = idempotency_key

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_url}/events",
                json=payload,
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    async def send_events_batch(
        self,
        events: list[dict[str, Any]],
        fail_fast: bool = False,
    ) -> dict[str, Any]:
        """Send multiple events in a batch."""
        payload = {
            "events": events,
            "fail_fast": fail_fast,
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_url}/events/batch",
                json=payload,
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    async def get_event(self, event_id: str) -> dict[str, Any]:
        """Get a specific event by ID."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_url}/events/{event_id}",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    async def list_events(
        self,
        event_type: str | None = None,
        source: str | None = None,
        status: str | None = None,
        limit: int = 100,
        cursor: str | None = None,
    ) -> dict[str, Any]:
        """List events with optional filters."""
        params = {"limit": limit}
        if event_type:
            params["event_type"] = event_type
        if source:
            params["source"] = source
        if status:
            params["status"] = status
        if cursor:
            params["cursor"] = cursor

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_url}/events",
                params=params,
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    async def replay_event(
        self,
        event_id: str,
        dry_run: bool = False,
        target_subscription_ids: list[str] | None = None,
        payload_override: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Replay an event."""
        payload = {"dry_run": dry_run}
        if target_subscription_ids:
            payload["target_subscription_ids"] = target_subscription_ids
        if payload_override:
            payload["payload_override"] = payload_override

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_url}/events/{event_id}/replay",
                json=payload,
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    # Inbox API

    async def list_inbox(
        self,
        subscription_id: str | None = None,
        event_type: str | None = None,
        limit: int = 100,
        visibility_timeout: int | None = None,
    ) -> dict[str, Any]:
        """List events in the inbox."""
        params = {"limit": limit}
        if subscription_id:
            params["subscription_id"] = subscription_id
        if event_type:
            params["event_type"] = event_type
        if visibility_timeout:
            params["visibility_timeout"] = visibility_timeout

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_url}/inbox",
                params=params,
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    async def acknowledge_events(
        self,
        receipt_handles: list[str],
    ) -> dict[str, Any]:
        """Acknowledge processed events."""
        payload = {"receipt_handles": receipt_handles}

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_url}/inbox/ack",
                json=payload,
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    async def get_inbox_stats(self) -> dict[str, Any]:
        """Get inbox statistics."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_url}/inbox/stats",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    # Subscriptions API

    async def list_subscriptions(
        self,
        limit: int = 100,
    ) -> dict[str, Any]:
        """List subscriptions."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_url}/subscriptions",
                params={"limit": limit},
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    async def get_subscription(self, subscription_id: str) -> dict[str, Any]:
        """Get a specific subscription."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_url}/subscriptions/{subscription_id}",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    # DLQ API

    async def list_dlq(
        self,
        event_type: str | None = None,
        source: str | None = None,
        limit: int = 100,
        offset: int = 0,
    ) -> dict[str, Any]:
        """List DLQ items."""
        params = {"limit": limit, "offset": offset}
        if event_type:
            params["event_type"] = event_type
        if source:
            params["source"] = source

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_url}/dlq",
                params=params,
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    async def retry_dlq_item(self, event_id: str) -> dict[str, Any]:
        """Retry a DLQ item."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.post(
                f"{self.api_url}/dlq/{event_id}/retry",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    async def dismiss_dlq_item(self, event_id: str) -> dict[str, Any]:
        """Dismiss a DLQ item."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.delete(
                f"{self.api_url}/dlq/{event_id}",
                headers=self._get_headers(),
            )
            return self._handle_response(response)

    # Streaming

    async def stream_events(
        self,
        subscription_id: str | None = None,
        event_types: list[str] | None = None,
    ) -> AsyncIterator[dict[str, Any]]:
        """Stream events using SSE."""
        params = {}
        if subscription_id:
            params["subscription_id"] = subscription_id
        if event_types:
            params["event_types"] = ",".join(event_types)

        headers = self._get_headers()
        headers["Accept"] = "text/event-stream"

        async with httpx.AsyncClient(timeout=None) as client:
            async with aconnect_sse(
                client,
                "GET",
                f"{self.api_url}/events/stream",
                params=params,
                headers=headers,
            ) as event_source:
                async for event in event_source.aiter_sse():
                    if event.data:
                        try:
                            yield json.loads(event.data)
                        except json.JSONDecodeError:
                            yield {"raw": event.data}

    # Health

    async def health_check(self) -> dict[str, Any]:
        """Check API health."""
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(
                f"{self.api_url}/health",
                headers=self._get_headers(),
            )
            return self._handle_response(response)
