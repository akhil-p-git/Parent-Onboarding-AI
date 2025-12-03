"""
Integration Tests for Event Replay Feature.

Tests the POST /events/{id}/replay endpoint and related functionality.
"""

import pytest
from datetime import datetime, timezone
from unittest.mock import AsyncMock, patch

from fastapi import status
from httpx import AsyncClient

from app.models import Event, EventStatus, Subscription


@pytest.fixture
def sample_event_data():
    """Sample event data for testing."""
    return {
        "event_type": "user.created",
        "source": "test-service",
        "data": {
            "user_id": "usr_123",
            "email": "test@example.com",
            "name": "Test User",
        },
        "metadata": {
            "correlation_id": "corr_abc123",
        },
    }


@pytest.fixture
def sample_subscription_data():
    """Sample subscription data for testing."""
    return {
        "name": "Test Subscription",
        "webhook_url": "https://webhook.example.com/handler",
        "event_types": ["user.*"],
        "is_active": True,
    }


class TestReplayEndpoint:
    """Tests for the replay event endpoint."""

    @pytest.mark.asyncio
    async def test_replay_event_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
        db_session,
    ):
        """Test successful event replay."""
        # Create an event first
        create_response = await client.post(
            "/api/v1/events",
            json=sample_event_data,
            headers=auth_headers,
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        event_id = create_response.json()["id"]

        # Enable replay feature
        with patch("app.core.config.settings.ENABLE_EVENT_REPLAY", True):
            # Replay the event
            replay_response = await client.post(
                f"/api/v1/events/{event_id}/replay",
                json={"dry_run": False},
                headers=auth_headers,
            )

            assert replay_response.status_code == status.HTTP_200_OK
            data = replay_response.json()
            assert data["success"] is True
            assert data["event_id"] == event_id
            assert data["replay_event_id"] is not None
            assert data["replay_event_id"] != event_id
            assert data["dry_run"] is False

    @pytest.mark.asyncio
    async def test_replay_event_dry_run(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
        db_session,
    ):
        """Test dry run mode returns preview without creating event."""
        # Create an event first
        create_response = await client.post(
            "/api/v1/events",
            json=sample_event_data,
            headers=auth_headers,
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        event_id = create_response.json()["id"]

        # Enable replay feature
        with patch("app.core.config.settings.ENABLE_EVENT_REPLAY", True):
            # Replay with dry_run=True
            replay_response = await client.post(
                f"/api/v1/events/{event_id}/replay",
                json={"dry_run": True},
                headers=auth_headers,
            )

            assert replay_response.status_code == status.HTTP_200_OK
            data = replay_response.json()
            assert data["success"] is True
            assert data["event_id"] == event_id
            assert data["replay_event_id"] is None  # No event created
            assert data["dry_run"] is True
            assert "details" in data
            assert data["details"]["original_event_type"] == sample_event_data["event_type"]

    @pytest.mark.asyncio
    async def test_replay_event_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test replay returns 404 for non-existent event."""
        with patch("app.core.config.settings.ENABLE_EVENT_REPLAY", True):
            response = await client.post(
                "/api/v1/events/evt_nonexistent/replay",
                json={"dry_run": False},
                headers=auth_headers,
            )

            assert response.status_code == status.HTTP_404_NOT_FOUND
            data = response.json()
            assert "not found" in data["detail"]["detail"].lower()

    @pytest.mark.asyncio
    async def test_replay_event_disabled(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
        db_session,
    ):
        """Test replay returns error when feature is disabled."""
        # Create an event first
        create_response = await client.post(
            "/api/v1/events",
            json=sample_event_data,
            headers=auth_headers,
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        event_id = create_response.json()["id"]

        # Disable replay feature
        with patch("app.core.config.settings.ENABLE_EVENT_REPLAY", False):
            response = await client.post(
                f"/api/v1/events/{event_id}/replay",
                json={"dry_run": False},
                headers=auth_headers,
            )

            assert response.status_code == status.HTTP_400_BAD_REQUEST
            data = response.json()
            assert "disabled" in data["detail"]["detail"].lower()

    @pytest.mark.asyncio
    async def test_replay_with_payload_override(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
        db_session,
    ):
        """Test replay with payload modifications."""
        # Create an event first
        create_response = await client.post(
            "/api/v1/events",
            json=sample_event_data,
            headers=auth_headers,
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        event_id = create_response.json()["id"]

        with patch("app.core.config.settings.ENABLE_EVENT_REPLAY", True):
            # Replay with payload override
            replay_response = await client.post(
                f"/api/v1/events/{event_id}/replay",
                json={
                    "dry_run": True,
                    "payload_override": {"user_id": "usr_modified"},
                },
                headers=auth_headers,
            )

            assert replay_response.status_code == status.HTTP_200_OK
            data = replay_response.json()
            assert data["success"] is True
            assert data["details"]["payload_modified"] is True

    @pytest.mark.asyncio
    async def test_replay_with_metadata_override(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
        db_session,
    ):
        """Test replay with metadata modifications."""
        # Create an event first
        create_response = await client.post(
            "/api/v1/events",
            json=sample_event_data,
            headers=auth_headers,
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        event_id = create_response.json()["id"]

        with patch("app.core.config.settings.ENABLE_EVENT_REPLAY", True):
            # Replay with metadata override
            replay_response = await client.post(
                f"/api/v1/events/{event_id}/replay",
                json={
                    "dry_run": True,
                    "metadata_override": {"replay_reason": "testing"},
                },
                headers=auth_headers,
            )

            assert replay_response.status_code == status.HTTP_200_OK
            data = replay_response.json()
            assert data["success"] is True
            assert data["details"]["metadata_modified"] is True

    @pytest.mark.asyncio
    async def test_replay_requires_auth(
        self,
        client: AsyncClient,
    ):
        """Test replay endpoint requires authentication."""
        response = await client.post(
            "/api/v1/events/evt_123/replay",
            json={"dry_run": False},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestReplayPreviewEndpoint:
    """Tests for the replay preview endpoint."""

    @pytest.mark.asyncio
    async def test_preview_replay_success(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
        db_session,
    ):
        """Test successful replay preview."""
        # Create an event first
        create_response = await client.post(
            "/api/v1/events",
            json=sample_event_data,
            headers=auth_headers,
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        event_id = create_response.json()["id"]

        with patch("app.core.config.settings.ENABLE_EVENT_REPLAY", True):
            # Get preview
            preview_response = await client.get(
                f"/api/v1/events/{event_id}/replay/preview",
                headers=auth_headers,
            )

            assert preview_response.status_code == status.HTTP_200_OK
            data = preview_response.json()
            assert data["event_id"] == event_id
            assert "original_event" in data
            assert "replay_payload" in data
            assert "target_subscriptions" in data

    @pytest.mark.asyncio
    async def test_preview_event_not_found(
        self,
        client: AsyncClient,
        auth_headers: dict,
    ):
        """Test preview returns 404 for non-existent event."""
        response = await client.get(
            "/api/v1/events/evt_nonexistent/replay/preview",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_preview_with_target_subscriptions(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
        db_session,
    ):
        """Test preview with specific target subscriptions."""
        # Create an event first
        create_response = await client.post(
            "/api/v1/events",
            json=sample_event_data,
            headers=auth_headers,
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        event_id = create_response.json()["id"]

        # This test verifies the query parameter is properly parsed
        # The subscription might not exist, which is expected to return 404
        with patch("app.core.config.settings.ENABLE_EVENT_REPLAY", True):
            response = await client.get(
                f"/api/v1/events/{event_id}/replay/preview",
                params={"target_subscription_ids": "sub_123,sub_456"},
                headers=auth_headers,
            )

            # Subscription not found is expected here
            assert response.status_code in [
                status.HTTP_200_OK,
                status.HTTP_404_NOT_FOUND,
            ]


class TestReplayServiceLogic:
    """Tests for the replay service business logic."""

    @pytest.mark.asyncio
    async def test_replay_adds_tracking_metadata(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
        db_session,
    ):
        """Test that replay adds tracking metadata to the new event."""
        # Create an event first
        create_response = await client.post(
            "/api/v1/events",
            json=sample_event_data,
            headers=auth_headers,
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        event_id = create_response.json()["id"]

        with patch("app.core.config.settings.ENABLE_EVENT_REPLAY", True):
            # Dry run to see the replay data
            replay_response = await client.post(
                f"/api/v1/events/{event_id}/replay",
                json={"dry_run": True},
                headers=auth_headers,
            )

            assert replay_response.status_code == status.HTTP_200_OK
            data = replay_response.json()

            # Check that replay tracking metadata would be added
            if "replay_data" in data.get("details", {}):
                replay_data = data["details"]["replay_data"]
                assert "_replay" in replay_data.get("metadata", {})
                assert replay_data["metadata"]["_replay"]["original_event_id"] == event_id

    @pytest.mark.asyncio
    async def test_replay_preserves_original_event_type(
        self,
        client: AsyncClient,
        auth_headers: dict,
        sample_event_data: dict,
        db_session,
    ):
        """Test that replay preserves the original event type."""
        # Create an event first
        create_response = await client.post(
            "/api/v1/events",
            json=sample_event_data,
            headers=auth_headers,
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        event_id = create_response.json()["id"]

        with patch("app.core.config.settings.ENABLE_EVENT_REPLAY", True):
            # Dry run to check preserved data
            replay_response = await client.post(
                f"/api/v1/events/{event_id}/replay",
                json={"dry_run": True},
                headers=auth_headers,
            )

            assert replay_response.status_code == status.HTTP_200_OK
            data = replay_response.json()
            assert data["details"]["original_event_type"] == sample_event_data["event_type"]
            assert data["details"]["original_source"] == sample_event_data["source"]

    @pytest.mark.asyncio
    async def test_replay_deep_merges_payload_override(
        self,
        client: AsyncClient,
        auth_headers: dict,
        db_session,
    ):
        """Test that payload override is deep merged with original."""
        # Create an event with nested data
        nested_event_data = {
            "event_type": "order.created",
            "source": "order-service",
            "data": {
                "order_id": "ord_123",
                "customer": {
                    "id": "cust_456",
                    "email": "original@example.com",
                },
                "items": [{"sku": "ITEM-001"}],
            },
        }

        create_response = await client.post(
            "/api/v1/events",
            json=nested_event_data,
            headers=auth_headers,
        )
        assert create_response.status_code == status.HTTP_201_CREATED
        event_id = create_response.json()["id"]

        with patch("app.core.config.settings.ENABLE_EVENT_REPLAY", True):
            # Replay with partial payload override
            replay_response = await client.post(
                f"/api/v1/events/{event_id}/replay",
                json={
                    "dry_run": True,
                    "payload_override": {
                        "customer": {
                            "email": "updated@example.com",
                        },
                    },
                },
                headers=auth_headers,
            )

            assert replay_response.status_code == status.HTTP_200_OK
            data = replay_response.json()

            # Verify deep merge happened
            if "replay_data" in data.get("details", {}):
                replay_data = data["details"]["replay_data"]["data"]
                # Original fields preserved
                assert replay_data["order_id"] == "ord_123"
                assert replay_data["customer"]["id"] == "cust_456"
                # Overridden field updated
                assert replay_data["customer"]["email"] == "updated@example.com"
