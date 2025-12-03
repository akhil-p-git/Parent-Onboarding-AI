"""
Integration tests for Events API endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestEventsAPI:
    """Integration tests for /api/v1/events endpoints."""

    async def test_create_event_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
    ):
        """Test successful event creation."""
        response = await async_client.post(
            "/api/v1/events",
            json=sample_event_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["id"].startswith("evt_")
        assert data["event_type"] == sample_event_data["event_type"]
        assert data["source"] == sample_event_data["source"]
        assert data["status"] == "pending"

    async def test_create_event_missing_event_type(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test event creation fails without event_type."""
        response = await async_client.post(
            "/api/v1/events",
            json={
                "source": "test",
                "data": {},
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    async def test_create_event_missing_source(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test event creation fails without source."""
        response = await async_client.post(
            "/api/v1/events",
            json={
                "event_type": "test.event",
                "data": {},
            },
            headers=auth_headers,
        )

        assert response.status_code == 422

    async def test_create_event_with_idempotency_key(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
    ):
        """Test event creation with idempotency key."""
        sample_event_data["idempotency_key"] = "test-idemp-key-123"

        response = await async_client.post(
            "/api/v1/events",
            json=sample_event_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["idempotency_key"] == "test-idemp-key-123"

    async def test_create_event_unauthorized(
        self,
        async_client: AsyncClient,
        sample_event_data: dict,
    ):
        """Test event creation without auth fails."""
        response = await async_client.post(
            "/api/v1/events",
            json=sample_event_data,
        )

        assert response.status_code == 401

    async def test_create_event_invalid_auth(
        self,
        async_client: AsyncClient,
        sample_event_data: dict,
    ):
        """Test event creation with invalid auth fails."""
        response = await async_client.post(
            "/api/v1/events",
            json=sample_event_data,
            headers={"Authorization": "Bearer invalid_key"},
        )

        assert response.status_code == 401

    async def test_get_event_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
    ):
        """Test getting an existing event."""
        # Create event first
        create_response = await async_client.post(
            "/api/v1/events",
            json=sample_event_data,
            headers=auth_headers,
        )
        event_id = create_response.json()["id"]

        # Get the event
        response = await async_client.get(
            f"/api/v1/events/{event_id}",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == event_id

    async def test_get_event_not_found(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test getting a non-existent event."""
        response = await async_client.get(
            "/api/v1/events/evt_nonexistent",
            headers=auth_headers,
        )

        assert response.status_code == 404

    async def test_list_events(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
    ):
        """Test listing events."""
        # Create a few events
        for i in range(3):
            data = sample_event_data.copy()
            data["data"] = {"index": i}
            await async_client.post(
                "/api/v1/events",
                json=data,
                headers=auth_headers,
            )

        # List events
        response = await async_client.get(
            "/api/v1/events",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert "pagination" in data
        assert len(data["data"]) >= 3

    async def test_list_events_with_filters(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test listing events with filters."""
        # Create events with different types
        await async_client.post(
            "/api/v1/events",
            json={
                "event_type": "user.created",
                "source": "user-service",
                "data": {},
            },
            headers=auth_headers,
        )
        await async_client.post(
            "/api/v1/events",
            json={
                "event_type": "order.created",
                "source": "order-service",
                "data": {},
            },
            headers=auth_headers,
        )

        # Filter by event_type
        response = await async_client.get(
            "/api/v1/events?type=user.created",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        for event in data["data"]:
            assert event["event_type"] == "user.created"

    async def test_list_events_pagination(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
    ):
        """Test event list pagination."""
        # Create multiple events
        for i in range(5):
            data = sample_event_data.copy()
            data["data"] = {"index": i}
            await async_client.post(
                "/api/v1/events",
                json=data,
                headers=auth_headers,
            )

        # Get first page
        response = await async_client.get(
            "/api/v1/events?limit=2",
            headers=auth_headers,
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["data"]) == 2
        assert data["pagination"]["has_more"] is True


@pytest.mark.integration
class TestBatchEventsAPI:
    """Integration tests for batch event endpoints."""

    async def test_create_batch_events_success(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test successful batch event creation."""
        batch_data = {
            "events": [
                {
                    "event_type": f"batch.event.{i}",
                    "source": "batch-test",
                    "data": {"index": i},
                }
                for i in range(5)
            ]
        }

        response = await async_client.post(
            "/api/v1/events/batch",
            json=batch_data,
            headers=auth_headers,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["summary"]["total"] == 5
        assert data["summary"]["successful"] == 5
        assert data["summary"]["failed"] == 0

    async def test_create_batch_events_partial_failure(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test batch with some invalid events."""
        batch_data = {
            "events": [
                {
                    "event_type": "valid.event",
                    "source": "test",
                    "data": {},
                },
                {
                    # Missing required fields - should fail validation
                    "data": {},
                },
            ]
        }

        response = await async_client.post(
            "/api/v1/events/batch",
            json=batch_data,
            headers=auth_headers,
        )

        # Batch endpoint may return 201 with partial success or 422 for validation
        assert response.status_code in [201, 422]

    async def test_create_batch_events_empty(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test batch with empty events list."""
        response = await async_client.post(
            "/api/v1/events/batch",
            json={"events": []},
            headers=auth_headers,
        )

        assert response.status_code == 422

    async def test_create_batch_events_exceeds_limit(
        self,
        async_client: AsyncClient,
        auth_headers: dict,
    ):
        """Test batch exceeding maximum size."""
        batch_data = {
            "events": [
                {
                    "event_type": f"event.{i}",
                    "source": "test",
                    "data": {},
                }
                for i in range(150)  # Exceeds 100 limit
            ]
        }

        response = await async_client.post(
            "/api/v1/events/batch",
            json=batch_data,
            headers=auth_headers,
        )

        assert response.status_code == 422
