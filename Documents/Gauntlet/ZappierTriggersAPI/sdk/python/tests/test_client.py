"""Tests for the TriggersClient."""

import pytest
import respx
from httpx import Response

from zapier_triggers import TriggersClient
from zapier_triggers.exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)


class TestTriggersClient:
    """Tests for TriggersClient."""

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TriggersClient(
            api_key="test_key",
            base_url="http://test-api.local",
        )

    @pytest.mark.asyncio
    async def test_client_context_manager(self):
        """Test client works as async context manager."""
        async with TriggersClient(api_key="test") as client:
            assert client._api_key == "test"

    @pytest.mark.asyncio
    async def test_client_builds_headers(self, client):
        """Test client builds correct headers."""
        headers = client._build_headers()

        assert headers["Authorization"] == "Bearer test_key"
        assert headers["Content-Type"] == "application/json"
        assert "User-Agent" in headers

    @pytest.mark.asyncio
    async def test_client_no_auth_header_without_key(self):
        """Test client doesn't include auth without key."""
        client = TriggersClient(base_url="http://test.local")
        headers = client._build_headers()

        assert "Authorization" not in headers

    @pytest.mark.asyncio
    @respx.mock
    async def test_request_success(self, client):
        """Test successful request."""
        respx.get("http://test-api.local/api/v1/health").mock(
            return_value=Response(200, json={"status": "healthy"})
        )

        async with client:
            result = await client.health()

        assert result["status"] == "healthy"

    @pytest.mark.asyncio
    @respx.mock
    async def test_handles_401_error(self, client):
        """Test handling of 401 authentication error."""
        respx.get("http://test-api.local/api/v1/events").mock(
            return_value=Response(
                401,
                json={"detail": {"detail": "Invalid API key"}},
            )
        )

        async with client:
            with pytest.raises(AuthenticationError) as exc_info:
                await client.request("GET", "/api/v1/events")

        assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    @respx.mock
    async def test_handles_404_error(self, client):
        """Test handling of 404 not found error."""
        respx.get("http://test-api.local/api/v1/events/evt_notfound").mock(
            return_value=Response(
                404,
                json={"detail": {"detail": "Event not found"}},
            )
        )

        async with client:
            with pytest.raises(NotFoundError) as exc_info:
                await client.request("GET", "/api/v1/events/evt_notfound")

        assert exc_info.value.status_code == 404

    @pytest.mark.asyncio
    @respx.mock
    async def test_handles_422_validation_error(self, client):
        """Test handling of 422 validation error."""
        respx.post("http://test-api.local/api/v1/events").mock(
            return_value=Response(
                422,
                json={
                    "detail": {
                        "detail": "Validation failed",
                        "errors": [{"field": "event_type", "message": "required"}],
                    }
                },
            )
        )

        async with client:
            with pytest.raises(ValidationError) as exc_info:
                await client.request("POST", "/api/v1/events", json={})

        assert exc_info.value.status_code == 422

    @pytest.mark.asyncio
    @respx.mock
    async def test_handles_429_rate_limit(self, client):
        """Test handling of 429 rate limit error."""
        respx.get("http://test-api.local/api/v1/events").mock(
            return_value=Response(
                429,
                json={"detail": {"detail": "Rate limit exceeded"}},
                headers={"Retry-After": "60"},
            )
        )

        async with client:
            with pytest.raises(RateLimitError) as exc_info:
                await client.request("GET", "/api/v1/events")

        assert exc_info.value.status_code == 429
        assert exc_info.value.retry_after == 60


class TestExceptions:
    """Tests for exception classes."""

    def test_api_error_str(self):
        """Test API error string representation."""
        error = AuthenticationError(
            message="Invalid key",
            status_code=401,
        )
        assert "[401] Invalid key" in str(error)

    def test_api_error_repr(self):
        """Test API error repr."""
        error = NotFoundError(
            message="Not found",
            status_code=404,
            error_type="not_found",
        )
        assert "NotFoundError" in repr(error)
        assert "404" in repr(error)

    def test_validation_error_fields(self):
        """Test validation error includes field errors."""
        error = ValidationError(
            message="Validation failed",
            status_code=422,
            validation_errors=[
                {"field": "email", "message": "invalid format"},
            ],
        )
        assert len(error.validation_errors) == 1
        assert error.validation_errors[0]["field"] == "email"

    def test_rate_limit_retry_after(self):
        """Test rate limit error includes retry_after."""
        error = RateLimitError(
            message="Too many requests",
            status_code=429,
            retry_after=30,
        )
        assert error.retry_after == 30
