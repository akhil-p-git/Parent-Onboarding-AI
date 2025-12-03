"""Tests for the Events resource."""

import pytest
import respx
from httpx import Response

from zapier_triggers import TriggersClient, Event, EventStatus


class TestEventsResource:
    """Tests for EventsResource."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TriggersClient(
            api_key="test_key",
            base_url="http://test-api.local",
        )

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_event(self, client):
        """Test creating an event."""
        respx.post("http://test-api.local/api/v1/events").mock(
            return_value=Response(
                201,
                json={
                    "id": "evt_123",
                    "event_type": "user.created",
                    "source": "test",
                    "data": {"user_id": "456"},
                    "metadata": None,
                    "status": "pending",
                    "idempotency_key": None,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": None,
                    "delivery_attempts": 0,
                    "successful_deliveries": 0,
                    "failed_deliveries": 0,
                },
            )
        )

        async with client:
            event = await client.events.create(
                event_type="user.created",
                source="test",
                data={"user_id": "456"},
            )

        assert event.id == "evt_123"
        assert event.event_type == "user.created"
        assert event.status == EventStatus.PENDING

    @pytest.mark.asyncio
    @respx.mock
    async def test_create_event_with_idempotency(self, client):
        """Test creating an event with idempotency key."""
        route = respx.post("http://test-api.local/api/v1/events").mock(
            return_value=Response(
                201,
                json={
                    "id": "evt_123",
                    "event_type": "user.created",
                    "source": "test",
                    "data": {},
                    "status": "pending",
                    "idempotency_key": "unique-key",
                    "created_at": "2024-01-01T00:00:00Z",
                    "delivery_attempts": 0,
                    "successful_deliveries": 0,
                    "failed_deliveries": 0,
                },
            )
        )

        async with client:
            event = await client.events.create(
                event_type="user.created",
                source="test",
                idempotency_key="unique-key",
            )

        assert route.called
        request_body = route.calls[0].request.content
        assert b"unique-key" in request_body

    @pytest.mark.asyncio
    @respx.mock
    async def test_get_event(self, client):
        """Test getting an event by ID."""
        respx.get("http://test-api.local/api/v1/events/evt_123").mock(
            return_value=Response(
                200,
                json={
                    "id": "evt_123",
                    "event_type": "user.created",
                    "source": "test",
                    "data": {"user_id": "456"},
                    "status": "delivered",
                    "created_at": "2024-01-01T00:00:00Z",
                    "delivery_attempts": 1,
                    "successful_deliveries": 1,
                    "failed_deliveries": 0,
                },
            )
        )

        async with client:
            event = await client.events.get("evt_123")

        assert event.id == "evt_123"
        assert event.status == EventStatus.DELIVERED

    @pytest.mark.asyncio
    @respx.mock
    async def test_list_events(self, client):
        """Test listing events."""
        respx.get("http://test-api.local/api/v1/events").mock(
            return_value=Response(
                200,
                json={
                    "data": [
                        {
                            "id": "evt_1",
                            "event_type": "user.created",
                            "source": "test",
                            "data": {},
                            "status": "pending",
                            "created_at": "2024-01-01T00:00:00Z",
                            "delivery_attempts": 0,
                            "successful_deliveries": 0,
                            "failed_deliveries": 0,
                        },
                        {
                            "id": "evt_2",
                            "event_type": "user.updated",
                            "source": "test",
                            "data": {},
                            "status": "delivered",
                            "created_at": "2024-01-01T00:00:00Z",
                            "delivery_attempts": 1,
                            "successful_deliveries": 1,
                            "failed_deliveries": 0,
                        },
                    ],
                    "pagination": {
                        "limit": 100,
                        "has_more": False,
                        "next_cursor": None,
                    },
                },
            )
        )

        async with client:
            result = await client.events.list()

        assert len(result.data) == 2
        assert result.data[0].id == "evt_1"
        assert result.pagination.has_more is False

    @pytest.mark.asyncio
    @respx.mock
    async def test_list_events_with_filters(self, client):
        """Test listing events with filters."""
        route = respx.get("http://test-api.local/api/v1/events").mock(
            return_value=Response(
                200,
                json={
                    "data": [],
                    "pagination": {"limit": 50, "has_more": False},
                },
            )
        )

        async with client:
            await client.events.list(
                event_type="user.created",
                source="auth",
                status=EventStatus.PENDING,
                limit=50,
            )

        assert route.called
        request = route.calls[0].request
        assert "event_type=user.created" in str(request.url)
        assert "source=auth" in str(request.url)
        assert "limit=50" in str(request.url)

    @pytest.mark.asyncio
    @respx.mock
    async def test_batch_create(self, client):
        """Test batch event creation."""
        respx.post("http://test-api.local/api/v1/events/batch").mock(
            return_value=Response(
                201,
                json={
                    "successful": 2,
                    "failed": 0,
                    "results": [
                        {
                            "index": 0,
                            "success": True,
                            "event": {
                                "id": "evt_1",
                                "event_type": "user.created",
                                "source": "test",
                                "data": {},
                                "status": "pending",
                                "created_at": "2024-01-01T00:00:00Z",
                                "delivery_attempts": 0,
                                "successful_deliveries": 0,
                                "failed_deliveries": 0,
                            },
                        },
                        {
                            "index": 1,
                            "success": True,
                            "event": {
                                "id": "evt_2",
                                "event_type": "user.created",
                                "source": "test",
                                "data": {},
                                "status": "pending",
                                "created_at": "2024-01-01T00:00:00Z",
                                "delivery_attempts": 0,
                                "successful_deliveries": 0,
                                "failed_deliveries": 0,
                            },
                        },
                    ],
                },
            )
        )

        async with client:
            result = await client.events.batch_create([
                {"event_type": "user.created", "source": "test", "data": {"id": "1"}},
                {"event_type": "user.created", "source": "test", "data": {"id": "2"}},
            ])

        assert result.successful == 2
        assert result.failed == 0
        assert len(result.results) == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_replay_event(self, client):
        """Test replaying an event."""
        respx.post("http://test-api.local/api/v1/events/evt_123/replay").mock(
            return_value=Response(
                200,
                json={
                    "success": True,
                    "event_id": "evt_123",
                    "replay_event_id": "evt_456",
                    "dry_run": False,
                    "target_subscriptions": ["sub_1", "sub_2"],
                },
            )
        )

        async with client:
            result = await client.events.replay("evt_123")

        assert result.success is True
        assert result.replay_event_id == "evt_456"
        assert len(result.target_subscriptions) == 2

    @pytest.mark.asyncio
    @respx.mock
    async def test_replay_event_dry_run(self, client):
        """Test replay with dry_run."""
        route = respx.post("http://test-api.local/api/v1/events/evt_123/replay").mock(
            return_value=Response(
                200,
                json={
                    "success": True,
                    "event_id": "evt_123",
                    "replay_event_id": None,
                    "dry_run": True,
                    "target_subscriptions": ["sub_1"],
                },
            )
        )

        async with client:
            result = await client.events.replay("evt_123", dry_run=True)

        assert result.dry_run is True
        assert result.replay_event_id is None

    @pytest.mark.asyncio
    @respx.mock
    async def test_iterate_events(self, client):
        """Test iterating over events."""
        # First page
        respx.get("http://test-api.local/api/v1/events").mock(
            side_effect=[
                Response(
                    200,
                    json={
                        "data": [
                            {
                                "id": "evt_1",
                                "event_type": "user.created",
                                "source": "test",
                                "data": {},
                                "status": "pending",
                                "created_at": "2024-01-01T00:00:00Z",
                                "delivery_attempts": 0,
                                "successful_deliveries": 0,
                                "failed_deliveries": 0,
                            },
                        ],
                        "pagination": {
                            "limit": 100,
                            "has_more": True,
                            "next_cursor": "cursor_1",
                        },
                    },
                ),
                Response(
                    200,
                    json={
                        "data": [
                            {
                                "id": "evt_2",
                                "event_type": "user.created",
                                "source": "test",
                                "data": {},
                                "status": "pending",
                                "created_at": "2024-01-01T00:00:00Z",
                                "delivery_attempts": 0,
                                "successful_deliveries": 0,
                                "failed_deliveries": 0,
                            },
                        ],
                        "pagination": {
                            "limit": 100,
                            "has_more": False,
                            "next_cursor": None,
                        },
                    },
                ),
            ]
        )

        async with client:
            events = []
            async for event in client.events.iterate():
                events.append(event)

        assert len(events) == 2
        assert events[0].id == "evt_1"
        assert events[1].id == "evt_2"
