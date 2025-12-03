"""
Tests for the Triggers API Client.
"""

import pytest
import respx
from httpx import Response

from triggers_cli.client import ApiError, TriggersClient
from triggers_cli.config import set_config


@pytest.fixture
def client():
    """Create a test client."""
    set_config(api_url="http://test-api.local", api_key="test_key")
    return TriggersClient(
        api_url="http://test-api.local",
        api_key="test_key",
    )


class TestTriggersClient:
    """Tests for TriggersClient."""

    @pytest.mark.asyncio
    @respx.mock
    async def test_send_event_success(self, client):
        """Test sending an event successfully."""
        respx.post("http://test-api.local/api/v1/events").mock(
            return_value=Response(
                201,
                json={
                    "id": "evt_123",
                    "event_type": "user.created",
                    "source": "test",
                    "status": "pending",
                },
            )
        )

        result = await client.send_event(
            event_type="user.created",
            source="test",
            data={"user_id": "123"},
        )

        assert result["id"] == "evt_123"
        assert result["status"] == "pending"

    @pytest.mark.asyncio
    @respx.mock
    async def test_send_event_error(self, client):
        """Test sending an event with API error."""
        respx.post("http://test-api.local/api/v1/events").mock(
            return_value=Response(
                400,
                json={
                    "detail": {
                        "detail": "Invalid event type",
                    }
                },
            )
        )

        with pytest.raises(ApiError) as exc_info:
            await client.send_event(
                event_type="invalid",
                source="test",
                data={},
            )

        assert exc_info.value.status_code == 400
        assert "Invalid event type" in exc_info.value.message

    @pytest.mark.asyncio
    @respx.mock
    async def test_list_events_success(self, client):
        """Test listing events."""
        respx.get("http://test-api.local/api/v1/events").mock(
            return_value=Response(
                200,
                json={
                    "data": [
                        {"id": "evt_1", "event_type": "user.created"},
                        {"id": "evt_2", "event_type": "order.completed"},
                    ],
                    "pagination": {"has_more": False},
                },
            )
        )

        result = await client.list_events()

        assert len(result["data"]) == 2
        assert result["data"][0]["id"] == "evt_1"

    @pytest.mark.asyncio
    @respx.mock
    async def test_list_events_with_filters(self, client):
        """Test listing events with filters."""
        route = respx.get("http://test-api.local/api/v1/events").mock(
            return_value=Response(
                200,
                json={"data": [], "pagination": {"has_more": False}},
            )
        )

        await client.list_events(
            event_type="user.created",
            source="auth",
            status="pending",
            limit=50,
        )

        assert route.called
        request = route.calls[0].request
        assert "event_type=user.created" in str(request.url)
        assert "source=auth" in str(request.url)
        assert "limit=50" in str(request.url)

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_event_success(self, client):
        """Test getting a specific event."""
        respx.get("http://test-api.local/api/v1/events/evt_123").mock(
            return_value=Response(
                200,
                json={
                    "id": "evt_123",
                    "event_type": "user.created",
                    "data": {"user_id": "456"},
                },
            )
        )

        result = await client.get_event("evt_123")

        assert result["id"] == "evt_123"
        assert result["data"]["user_id"] == "456"

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_event_not_found(self, client):
        """Test getting a non-existent event."""
        respx.get("http://test-api.local/api/v1/events/evt_notfound").mock(
            return_value=Response(
                404,
                json={"detail": {"detail": "Event not found"}},
            )
        )

        with pytest.raises(ApiError) as exc_info:
            await client.get_event("evt_notfound")

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @respx.mock
    async def test_list_inbox_success(self, client):
        """Test listing inbox."""
        respx.get("http://test-api.local/api/v1/inbox").mock(
            return_value=Response(
                200,
                json={
                    "data": [
                        {
                            "event_id": "evt_1",
                            "receipt_handle": "rh_123",
                        }
                    ],
                },
            )
        )

        result = await client.list_inbox()

        assert len(result["data"]) == 1
        assert result["data"][0]["receipt_handle"] == "rh_123"

    @pytest.mark.asyncio
    @respx.mock
    async def test_acknowledge_events_success(self, client):
        """Test acknowledging events."""
        respx.post("http://test-api.local/api/v1/inbox/ack").mock(
            return_value=Response(
                200,
                json={"successful": 2, "failed": 0},
            )
        )

        result = await client.acknowledge_events(["rh_1", "rh_2"])

        assert result["successful"] == 2
        assert result["failed"] == 0

    @pytest.mark.asyncio
    @respx.mock
    async def test_list_dlq_success(self, client):
        """Test listing DLQ."""
        respx.get("http://test-api.local/api/v1/dlq").mock(
            return_value=Response(
                200,
                json={
                    "data": [{"event_id": "evt_1", "retry_count": 3}],
                    "pagination": {"total": 1},
                },
            )
        )

        result = await client.list_dlq()

        assert len(result["data"]) == 1
        assert result["data"][0]["retry_count"] == 3

    @pytest.mark.asyncio
    @respx.mock
    async def test_retry_dlq_item_success(self, client):
        """Test retrying a DLQ item."""
        respx.post("http://test-api.local/api/v1/dlq/evt_123/retry").mock(
            return_value=Response(
                200,
                json={"success": True, "event_id": "evt_123"},
            )
        )

        result = await client.retry_dlq_item("evt_123")

        assert result["success"] is True

    @pytest.mark.asyncio
    @respx.mock
    async def test_health_check_success(self, client):
        """Test health check."""
        respx.get("http://test-api.local/api/v1/health").mock(
            return_value=Response(
                200,
                json={
                    "status": "healthy",
                    "version": "1.0.0",
                },
            )
        )

        result = await client.health_check()

        assert result["status"] == "healthy"

    def test_client_headers(self, client):
        """Test client headers include auth."""
        headers = client._get_headers()

        assert headers["Authorization"] == "Bearer test_key"
        assert headers["Content-Type"] == "application/json"

    def test_client_no_auth(self):
        """Test client without auth key."""
        client = TriggersClient(api_url="http://test.local", api_key=None)
        headers = client._get_headers()

        assert "Authorization" not in headers
