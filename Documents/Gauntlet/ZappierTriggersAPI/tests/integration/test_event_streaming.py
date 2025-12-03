"""
Integration tests for Event Streaming (SSE) endpoints.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app
from app.services.streaming_service import StreamingService


class TestEventStreaming:
    """Tests for event streaming endpoints."""

    @pytest.fixture
    def mock_streaming_service(self):
        """Create a mock streaming service."""
        service = AsyncMock(spec=StreamingService)
        return service

    @pytest.fixture
    def auth_headers(self):
        """Create authentication headers."""
        return {"Authorization": "Bearer test_api_key"}

    @pytest.mark.asyncio
    async def test_stream_endpoint_returns_sse_content_type(self, auth_headers):
        """Test that stream endpoint returns text/event-stream content type."""
        # Mock the authentication and streaming service
        async def mock_stream_events(**kwargs):
            yield {
                "event": "connected",
                "data": {"message": "Connected"},
            }

        with patch("app.api.v1.endpoints.events.get_streaming_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_service.stream_events = mock_stream_events
            mock_get_service.return_value = mock_service

            with patch("app.api.deps.get_api_key_from_header") as mock_auth:
                mock_key = MagicMock()
                mock_key.id = "key_123"
                mock_key.scopes = ["events:read"]
                mock_auth.return_value = mock_key

                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                ) as client:
                    # Use stream=True to handle SSE
                    async with client.stream(
                        "GET",
                        f"{settings.API_V1_PREFIX}/events/stream",
                        headers=auth_headers,
                    ) as response:
                        assert response.status_code == 200
                        assert "text/event-stream" in response.headers.get(
                            "content-type", ""
                        )

    @pytest.mark.asyncio
    async def test_stream_endpoint_requires_authentication(self):
        """Test that stream endpoint requires authentication."""
        async with AsyncClient(
            transport=ASGITransport(app=app),
            base_url="http://test",
        ) as client:
            response = await client.get(f"{settings.API_V1_PREFIX}/events/stream")
            # Should return 401 or 403 without auth
            assert response.status_code in [401, 403]

    @pytest.mark.asyncio
    async def test_stream_accepts_event_type_filter(self, auth_headers):
        """Test that stream endpoint accepts event type filter."""
        received_filters = {}

        async def mock_stream_events(event_types=None, sources=None, subscription_id=None):
            received_filters["event_types"] = event_types
            received_filters["sources"] = sources
            received_filters["subscription_id"] = subscription_id
            yield {
                "event": "connected",
                "data": {"filters": {"event_types": event_types}},
            }

        with patch("app.api.v1.endpoints.events.get_streaming_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_service.stream_events = mock_stream_events
            mock_get_service.return_value = mock_service

            with patch("app.api.deps.get_api_key_from_header") as mock_auth:
                mock_key = MagicMock()
                mock_key.id = "key_123"
                mock_key.scopes = ["events:read"]
                mock_auth.return_value = mock_key

                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                ) as client:
                    async with client.stream(
                        "GET",
                        f"{settings.API_V1_PREFIX}/events/stream?event_types=user.*,order.created",
                        headers=auth_headers,
                    ) as response:
                        assert response.status_code == 200
                        # Read first chunk to trigger the generator
                        async for _ in response.aiter_bytes():
                            break

                # Verify filters were passed correctly
                assert received_filters["event_types"] == ["user.*", "order.created"]

    @pytest.mark.asyncio
    async def test_stream_accepts_source_filter(self, auth_headers):
        """Test that stream endpoint accepts source filter."""
        received_filters = {}

        async def mock_stream_events(event_types=None, sources=None, subscription_id=None):
            received_filters["sources"] = sources
            yield {
                "event": "connected",
                "data": {"filters": {"sources": sources}},
            }

        with patch("app.api.v1.endpoints.events.get_streaming_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_service.stream_events = mock_stream_events
            mock_get_service.return_value = mock_service

            with patch("app.api.deps.get_api_key_from_header") as mock_auth:
                mock_key = MagicMock()
                mock_key.id = "key_123"
                mock_key.scopes = ["events:read"]
                mock_auth.return_value = mock_key

                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                ) as client:
                    async with client.stream(
                        "GET",
                        f"{settings.API_V1_PREFIX}/events/stream?sources=auth-service,payments",
                        headers=auth_headers,
                    ) as response:
                        assert response.status_code == 200
                        async for _ in response.aiter_bytes():
                            break

                assert received_filters["sources"] == ["auth-service", "payments"]

    @pytest.mark.asyncio
    async def test_stream_accepts_subscription_filter(self, auth_headers):
        """Test that stream endpoint accepts subscription filter."""
        received_filters = {}

        async def mock_stream_events(event_types=None, sources=None, subscription_id=None):
            received_filters["subscription_id"] = subscription_id
            yield {
                "event": "connected",
                "data": {"filters": {"subscription_id": subscription_id}},
            }

        with patch("app.api.v1.endpoints.events.get_streaming_service") as mock_get_service:
            mock_service = AsyncMock()
            mock_service.stream_events = mock_stream_events
            mock_get_service.return_value = mock_service

            with patch("app.api.deps.get_api_key_from_header") as mock_auth:
                mock_key = MagicMock()
                mock_key.id = "key_123"
                mock_key.scopes = ["events:read"]
                mock_auth.return_value = mock_key

                async with AsyncClient(
                    transport=ASGITransport(app=app),
                    base_url="http://test",
                ) as client:
                    async with client.stream(
                        "GET",
                        f"{settings.API_V1_PREFIX}/events/stream?subscription_id=sub_123",
                        headers=auth_headers,
                    ) as response:
                        assert response.status_code == 200
                        async for _ in response.aiter_bytes():
                            break

                assert received_filters["subscription_id"] == "sub_123"


class TestStreamingServiceUnit:
    """Unit tests for StreamingService."""

    def test_matches_patterns_exact_match(self):
        """Test exact pattern matching."""
        service = StreamingService()

        assert service._matches_patterns("user.created", ["user.created"]) is True
        assert service._matches_patterns("user.updated", ["user.created"]) is False

    def test_matches_patterns_wildcard_suffix(self):
        """Test wildcard suffix pattern matching."""
        service = StreamingService()

        assert service._matches_patterns("user.created", ["user.*"]) is True
        assert service._matches_patterns("user.updated", ["user.*"]) is True
        assert service._matches_patterns("order.created", ["user.*"]) is False

    def test_matches_patterns_wildcard_prefix(self):
        """Test wildcard prefix pattern matching."""
        service = StreamingService()

        assert service._matches_patterns("user.created", ["*.created"]) is True
        assert service._matches_patterns("order.created", ["*.created"]) is True
        assert service._matches_patterns("user.updated", ["*.created"]) is False

    def test_matches_patterns_multiple_patterns(self):
        """Test matching against multiple patterns."""
        service = StreamingService()

        patterns = ["user.*", "order.completed"]
        assert service._matches_patterns("user.created", patterns) is True
        assert service._matches_patterns("order.completed", patterns) is True
        assert service._matches_patterns("payment.processed", patterns) is False

    def test_matches_filters_no_filters(self):
        """Test that all events match when no filters are specified."""
        service = StreamingService()
        event = {"event_type": "user.created", "source": "auth"}

        assert service._matches_filters(event, None, None, None) is True

    def test_matches_filters_event_type_filter(self):
        """Test event type filtering."""
        service = StreamingService()
        event = {"event_type": "user.created", "source": "auth"}

        assert service._matches_filters(event, ["user.*"], None, None) is True
        assert service._matches_filters(event, ["order.*"], None, None) is False

    def test_matches_filters_source_filter(self):
        """Test source filtering."""
        service = StreamingService()
        event = {"event_type": "user.created", "source": "auth-service"}

        assert service._matches_filters(event, None, ["auth*"], None) is False
        assert service._matches_filters(event, None, ["auth-service"], None) is True

    def test_matches_filters_subscription_filter(self):
        """Test subscription ID filtering."""
        service = StreamingService()

        # Event with subscription in _target_subscriptions
        event1 = {
            "event_type": "user.created",
            "_target_subscriptions": ["sub_123", "sub_456"],
        }
        assert service._matches_filters(event1, None, None, "sub_123") is True
        assert service._matches_filters(event1, None, None, "sub_789") is False

        # Event with subscription in metadata
        event2 = {
            "event_type": "user.created",
            "metadata": {"subscription_id": "sub_abc"},
        }
        assert service._matches_filters(event2, None, None, "sub_abc") is True
        assert service._matches_filters(event2, None, None, "sub_xyz") is False

    def test_matches_filters_combined_filters(self):
        """Test combined filters."""
        service = StreamingService()
        event = {
            "event_type": "user.created",
            "source": "auth-service",
            "_target_subscriptions": ["sub_123"],
        }

        # All filters match
        assert service._matches_filters(
            event, ["user.*"], ["auth-service"], "sub_123"
        ) is True

        # Event type doesn't match
        assert service._matches_filters(
            event, ["order.*"], ["auth-service"], "sub_123"
        ) is False

        # Source doesn't match
        assert service._matches_filters(
            event, ["user.*"], ["payment-service"], "sub_123"
        ) is False

        # Subscription doesn't match
        assert service._matches_filters(
            event, ["user.*"], ["auth-service"], "sub_999"
        ) is False


class TestStreamingServiceIntegration:
    """Integration tests for StreamingService with Redis."""

    @pytest.mark.asyncio
    async def test_publish_event(self):
        """Test publishing an event to the stream."""
        with patch("app.services.streaming_service.get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_get_redis.return_value = mock_redis

            service = StreamingService()
            event = {
                "id": "evt_123",
                "event_type": "user.created",
                "data": {"user_id": "123"},
            }

            await service.publish_event(event)

            # Verify publish was called with correct channel and data
            mock_redis.publish.assert_called_once()
            call_args = mock_redis.publish.call_args
            assert call_args[0][0] == StreamingService.EVENTS_CHANNEL
            published_data = json.loads(call_args[0][1])
            assert published_data["id"] == "evt_123"

    @pytest.mark.asyncio
    async def test_stream_events_yields_connected_event(self):
        """Test that stream_events yields a connected event first."""
        with patch("app.services.streaming_service.get_redis") as mock_get_redis:
            mock_redis = AsyncMock()
            mock_pubsub = AsyncMock()
            mock_pubsub.subscribe = AsyncMock()
            mock_pubsub.unsubscribe = AsyncMock()
            mock_pubsub.close = AsyncMock()

            # Make get_message return None to trigger heartbeat, then cancel
            call_count = 0
            async def mock_get_message(**kwargs):
                nonlocal call_count
                call_count += 1
                if call_count == 1:
                    return None  # Will yield connected event
                raise asyncio.CancelledError()

            mock_pubsub.get_message = mock_get_message
            mock_redis.pubsub.return_value = mock_pubsub
            mock_get_redis.return_value = mock_redis

            service = StreamingService()

            events = []
            try:
                async for event in service.stream_events():
                    events.append(event)
                    if len(events) >= 2:  # Get connected + heartbeat
                        break
            except asyncio.CancelledError:
                pass

            # First event should be "connected"
            assert len(events) >= 1
            assert events[0]["event"] == "connected"
            assert "message" in events[0]["data"]
