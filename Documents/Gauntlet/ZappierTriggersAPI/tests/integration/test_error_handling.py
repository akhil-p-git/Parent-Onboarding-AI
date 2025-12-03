"""
Integration tests for error handling and exception handlers.
"""

import pytest
from fastapi import APIRouter, HTTPException
from fastapi.testclient import TestClient
from httpx import AsyncClient

from app.core.exceptions import (
    AuthenticationError,
    NotFoundError,
    RateLimitError,
    ValidationError,
)


class TestExceptionHandlerIntegration:
    """Integration tests for exception handlers."""

    @pytest.mark.asyncio
    async def test_validation_error_response_format(
        self, async_client: AsyncClient, test_api_key: str
    ):
        """Test that validation errors return RFC 7807 format."""
        # Send invalid event data (missing required fields)
        response = await async_client.post(
            "/api/v1/events",
            json={"invalid": "data"},  # Missing event_type
            headers={"Authorization": f"Bearer {test_api_key}"},
        )

        assert response.status_code == 422
        data = response.json()

        # Check RFC 7807 structure
        assert "type" in data
        assert "title" in data
        assert "status" in data
        assert "detail" in data
        assert "error_code" in data
        assert data["status"] == 422

    @pytest.mark.asyncio
    async def test_not_found_error_format(
        self, async_client: AsyncClient, test_api_key: str
    ):
        """Test 404 error response format."""
        response = await async_client.get(
            "/api/v1/events/nonexistent-event-id",
            headers={"Authorization": f"Bearer {test_api_key}"},
        )

        assert response.status_code == 404
        data = response.json()

        assert "type" in data
        assert "title" in data
        assert data["status"] == 404
        assert "error_code" in data

    @pytest.mark.asyncio
    async def test_authentication_error_format(self, async_client: AsyncClient):
        """Test 401 error response format."""
        # Request without authentication
        response = await async_client.get("/api/v1/events")

        assert response.status_code == 401
        data = response.json()

        assert "type" in data
        assert "title" in data
        assert data["status"] == 401

    @pytest.mark.asyncio
    async def test_invalid_api_key_format(self, async_client: AsyncClient):
        """Test invalid API key error format."""
        response = await async_client.get(
            "/api/v1/events",
            headers={"Authorization": "Bearer invalid_key"},
        )

        assert response.status_code == 401
        data = response.json()

        assert data["status"] == 401
        assert "error_code" in data

    @pytest.mark.asyncio
    async def test_request_id_in_error_response(
        self, async_client: AsyncClient, test_api_key: str
    ):
        """Test that request ID is included in error responses."""
        response = await async_client.get(
            "/api/v1/events/nonexistent",
            headers={
                "Authorization": f"Bearer {test_api_key}",
                "X-Request-ID": "test-request-123",
            },
        )

        data = response.json()

        # Request ID should be in the response
        assert response.headers.get("X-Request-ID") == "test-request-123"

    @pytest.mark.asyncio
    async def test_validation_error_details(
        self, async_client: AsyncClient, test_api_key: str
    ):
        """Test that validation errors include field details."""
        response = await async_client.post(
            "/api/v1/events",
            json={},  # Empty body
            headers={"Authorization": f"Bearer {test_api_key}"},
        )

        assert response.status_code == 422
        data = response.json()

        # Should have validation error details
        assert "errors" in data
        assert "validation_errors" in data["errors"]
        assert len(data["errors"]["validation_errors"]) > 0

        # Each error should have field and message
        for error in data["errors"]["validation_errors"]:
            assert "field" in error
            assert "message" in error


class TestSecurityHeaders:
    """Tests for security headers middleware."""

    @pytest.mark.asyncio
    async def test_security_headers_present(self, async_client: AsyncClient):
        """Test that security headers are added to responses."""
        response = await async_client.get("/health")

        # Check security headers
        assert response.headers.get("X-Content-Type-Options") == "nosniff"
        assert response.headers.get("X-Frame-Options") == "DENY"
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"

    @pytest.mark.asyncio
    async def test_response_time_header(self, async_client: AsyncClient):
        """Test that response time header is added."""
        response = await async_client.get("/health")

        response_time = response.headers.get("X-Response-Time")
        assert response_time is not None
        assert response_time.endswith("ms")


class TestRequestLogging:
    """Tests for request/response logging middleware."""

    @pytest.mark.asyncio
    async def test_request_id_generated(self, async_client: AsyncClient):
        """Test that request ID is generated if not provided."""
        response = await async_client.get("/health")

        request_id = response.headers.get("X-Request-ID")
        assert request_id is not None
        assert len(request_id) == 36  # UUID format

    @pytest.mark.asyncio
    async def test_request_id_preserved(self, async_client: AsyncClient):
        """Test that provided request ID is preserved."""
        custom_id = "my-custom-request-id-123"
        response = await async_client.get(
            "/health",
            headers={"X-Request-ID": custom_id},
        )

        assert response.headers.get("X-Request-ID") == custom_id

    @pytest.mark.asyncio
    async def test_trace_id_propagated(self, async_client: AsyncClient):
        """Test that trace ID is propagated if provided."""
        trace_id = "my-trace-id-456"
        response = await async_client.get(
            "/health",
            headers={"X-Trace-ID": trace_id},
        )

        assert response.headers.get("X-Trace-ID") == trace_id


class TestErrorCodeConsistency:
    """Tests to ensure error codes are consistent."""

    @pytest.mark.asyncio
    async def test_401_error_code(self, async_client: AsyncClient):
        """Test 401 returns correct error code."""
        response = await async_client.get("/api/v1/events")

        data = response.json()
        assert data["error_code"] in [
            "authentication_required",
            "invalid_api_key",
        ]

    @pytest.mark.asyncio
    async def test_404_error_code(
        self, async_client: AsyncClient, test_api_key: str
    ):
        """Test 404 returns correct error code."""
        response = await async_client.get(
            "/api/v1/events/does-not-exist",
            headers={"Authorization": f"Bearer {test_api_key}"},
        )

        data = response.json()
        assert data["error_code"] == "resource_not_found"

    @pytest.mark.asyncio
    async def test_422_error_code(
        self, async_client: AsyncClient, test_api_key: str
    ):
        """Test 422 returns correct error code."""
        response = await async_client.post(
            "/api/v1/events",
            json={"bad": "data"},
            headers={"Authorization": f"Bearer {test_api_key}"},
        )

        data = response.json()
        assert data["error_code"] == "validation_error"
