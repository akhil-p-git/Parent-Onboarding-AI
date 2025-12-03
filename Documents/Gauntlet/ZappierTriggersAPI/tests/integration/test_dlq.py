"""
Integration Tests for Dead Letter Queue Management.

Tests the DLQ API endpoints for listing, retrying, and dismissing items.
"""

import json
import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from fastapi import status
from httpx import AsyncClient


@pytest.fixture
def sample_dlq_message():
    """Sample DLQ message for testing."""
    return {
        "event_id": "evt_test123",
        "event_type": "user.created",
        "source": "test-service",
        "created_at": datetime.now(timezone.utc).isoformat(),
        "enqueued_at": datetime.now(timezone.utc).isoformat(),
        "failure_reason": "Connection timeout",
        "retry_count": 3,
    }


@pytest.fixture
async def dlq_with_items(sample_dlq_message):
    """Fixture to populate DLQ with test items."""
    from app.core.redis import get_redis

    redis = await get_redis()
    dlq_key = "queue:events:dlq"

    # Clear any existing items
    await redis.delete(dlq_key)

    # Add test items
    messages = [
        {**sample_dlq_message, "event_id": f"evt_test{i}", "event_type": f"event.type{i % 3}"}
        for i in range(5)
    ]

    for msg in messages:
        await redis.lpush(dlq_key, json.dumps(msg))

    yield messages

    # Cleanup
    await redis.delete(dlq_key)


class TestDLQListEndpoint:
    """Tests for GET /dlq endpoint."""

    @pytest.mark.asyncio
    async def test_list_dlq_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test listing empty DLQ."""
        # Ensure DLQ is empty
        from app.core.redis import get_redis
        redis = await get_redis()
        await redis.delete("queue:events:dlq")

        response = await client.get(
            "/api/v1/dlq",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["data"] == []
        assert data["pagination"]["has_more"] is False

    @pytest.mark.asyncio
    async def test_list_dlq_with_items(
        self,
        client: AsyncClient,
        auth_headers: dict,
        dlq_with_items: list,
    ):
        """Test listing DLQ with items."""
        response = await client.get(
            "/api/v1/dlq",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) == 5
        assert data["pagination"]["total"] == 5

    @pytest.mark.asyncio
    async def test_list_dlq_with_pagination(
        self,
        client: AsyncClient,
        auth_headers: dict,
        dlq_with_items: list,
    ):
        """Test DLQ pagination."""
        response = await client.get(
            "/api/v1/dlq",
            params={"limit": 2, "offset": 0},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data["data"]) == 2
        assert data["pagination"]["has_more"] is True

    @pytest.mark.asyncio
    async def test_list_dlq_with_event_type_filter(
        self,
        client: AsyncClient,
        auth_headers: dict,
        dlq_with_items: list,
    ):
        """Test filtering DLQ by event type."""
        response = await client.get(
            "/api/v1/dlq",
            params={"event_type": "event.type0"},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        # Should only have items with event_type0 (indices 0, 3)
        for item in data["data"]:
            assert item["event_type"] == "event.type0"

    @pytest.mark.asyncio
    async def test_list_dlq_requires_auth(
        self,
        client: AsyncClient,
    ):
        """Test DLQ list requires authentication."""
        response = await client.get("/api/v1/dlq")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestDLQStatsEndpoint:
    """Tests for GET /dlq/stats endpoint."""

    @pytest.mark.asyncio
    async def test_get_dlq_stats(
        self,
        client: AsyncClient,
        auth_headers: dict,
        dlq_with_items: list,
    ):
        """Test getting DLQ statistics."""
        response = await client.get(
            "/api/v1/dlq/stats",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 5
        assert "by_event_type" in data
        assert "by_source" in data

    @pytest.mark.asyncio
    async def test_get_dlq_stats_empty(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting stats for empty DLQ."""
        from app.core.redis import get_redis
        redis = await get_redis()
        await redis.delete("queue:events:dlq")

        response = await client.get(
            "/api/v1/dlq/stats",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 0


class TestDLQGetItemEndpoint:
    """Tests for GET /dlq/{event_id} endpoint."""

    @pytest.mark.asyncio
    async def test_get_dlq_item(
        self,
        client: AsyncClient,
        auth_headers: dict,
        dlq_with_items: list,
    ):
        """Test getting a specific DLQ item."""
        response = await client.get(
            "/api/v1/dlq/evt_test0",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["event_id"] == "evt_test0"

    @pytest.mark.asyncio
    async def test_get_dlq_item_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting non-existent DLQ item."""
        response = await client.get(
            "/api/v1/dlq/evt_nonexistent",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestDLQRetryEndpoint:
    """Tests for POST /dlq/{event_id}/retry endpoint."""

    @pytest.mark.asyncio
    async def test_retry_dlq_item(
        self,
        client: AsyncClient,
        auth_headers: dict,
        dlq_with_items: list,
    ):
        """Test retrying a DLQ item."""
        from app.core.redis import get_redis
        redis = await get_redis()

        # Get initial queue length
        initial_queue_len = await redis.llen("queue:events")
        initial_dlq_len = await redis.llen("queue:events:dlq")

        response = await client.post(
            "/api/v1/dlq/evt_test0/retry",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["event_id"] == "evt_test0"
        assert data["retry_count"] >= 1

        # Verify item moved from DLQ to main queue
        new_queue_len = await redis.llen("queue:events")
        new_dlq_len = await redis.llen("queue:events:dlq")
        assert new_queue_len == initial_queue_len + 1
        assert new_dlq_len == initial_dlq_len - 1

    @pytest.mark.asyncio
    async def test_retry_dlq_item_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test retrying non-existent DLQ item."""
        response = await client.post(
            "/api/v1/dlq/evt_nonexistent/retry",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_retry_dlq_batch(
        self,
        client: AsyncClient,
        auth_headers: dict,
        dlq_with_items: list,
    ):
        """Test batch retry of DLQ items."""
        response = await client.post(
            "/api/v1/dlq/retry/batch",
            json={"event_ids": ["evt_test0", "evt_test1", "evt_nonexistent"]},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 3
        assert data["successful"] == 2
        assert data["failed"] == 1


class TestDLQDismissEndpoint:
    """Tests for DELETE /dlq/{event_id} endpoint."""

    @pytest.mark.asyncio
    async def test_dismiss_dlq_item(
        self,
        client: AsyncClient,
        auth_headers: dict,
        dlq_with_items: list,
    ):
        """Test dismissing a DLQ item."""
        from app.core.redis import get_redis
        redis = await get_redis()

        initial_dlq_len = await redis.llen("queue:events:dlq")

        response = await client.delete(
            "/api/v1/dlq/evt_test0",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["event_id"] == "evt_test0"

        # Verify item removed from DLQ
        new_dlq_len = await redis.llen("queue:events:dlq")
        assert new_dlq_len == initial_dlq_len - 1

    @pytest.mark.asyncio
    async def test_dismiss_dlq_item_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test dismissing non-existent DLQ item."""
        response = await client.delete(
            "/api/v1/dlq/evt_nonexistent",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_dismiss_dlq_batch(
        self,
        client: AsyncClient,
        auth_headers: dict,
        dlq_with_items: list,
    ):
        """Test batch dismiss of DLQ items."""
        response = await client.post(
            "/api/v1/dlq/dismiss/batch",
            json={"event_ids": ["evt_test0", "evt_test1"]},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["total"] == 2
        assert data["successful"] == 2


class TestDLQPurgeEndpoint:
    """Tests for DELETE /dlq endpoint."""

    @pytest.mark.asyncio
    async def test_purge_dlq_without_confirm(
        self,
        client: AsyncClient,
        auth_headers: dict,
        dlq_with_items: list,
    ):
        """Test purge requires confirmation."""
        response = await client.delete(
            "/api/v1/dlq",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        data = response.json()
        assert "confirm" in data["detail"]["detail"].lower()

    @pytest.mark.asyncio
    async def test_purge_dlq_with_confirm(
        self,
        client: AsyncClient,
        auth_headers: dict,
        dlq_with_items: list,
    ):
        """Test purging all DLQ items."""
        from app.core.redis import get_redis
        redis = await get_redis()

        response = await client.delete(
            "/api/v1/dlq",
            params={"confirm": "true"},
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["success"] is True
        assert data["purged_count"] == 5

        # Verify DLQ is empty
        dlq_len = await redis.llen("queue:events:dlq")
        assert dlq_len == 0
