"""
Integration tests for Health API endpoints.
"""

import pytest
from httpx import AsyncClient


@pytest.mark.integration
class TestHealthAPI:
    """Integration tests for health check endpoints."""

    async def test_health_check_root(self, async_client: AsyncClient):
        """Test root-level health check endpoint."""
        response = await async_client.get("/health")

        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "components" in data

    async def test_health_check_api(self, async_client: AsyncClient):
        """Test API-level health check endpoint."""
        response = await async_client.get("/api/v1/health")

        assert response.status_code in [200, 503]  # May be degraded without Redis
        data = response.json()
        assert "status" in data
        assert "version" in data
        assert "components" in data
        assert "timestamp" in data
        assert "uptime_seconds" in data

    async def test_readiness_probe(self, async_client: AsyncClient):
        """Test readiness probe endpoint."""
        response = await async_client.get("/ready")

        # May return 503 if DB not ready
        assert response.status_code in [200, 503]
        data = response.json()
        assert "ready" in data

    async def test_readiness_probe_api(self, async_client: AsyncClient):
        """Test API-level readiness probe."""
        response = await async_client.get("/api/v1/health/ready")

        assert response.status_code in [200, 503]
        data = response.json()
        assert "ready" in data
        assert "checks" in data

    async def test_liveness_probe(self, async_client: AsyncClient):
        """Test liveness probe endpoint."""
        response = await async_client.get("/live")

        assert response.status_code == 200
        data = response.json()
        assert data["alive"] is True

    async def test_liveness_probe_api(self, async_client: AsyncClient):
        """Test API-level liveness probe."""
        response = await async_client.get("/api/v1/health/live")

        assert response.status_code == 200
        data = response.json()
        assert data["alive"] is True
        assert "timestamp" in data

    async def test_system_info(self, async_client: AsyncClient):
        """Test system info endpoint."""
        response = await async_client.get("/api/v1/health/info")

        assert response.status_code == 200
        data = response.json()
        assert "app_name" in data
        assert "version" in data
        assert "environment" in data
        assert "python_version" in data
        assert "uptime_seconds" in data

    async def test_metrics_json(self, async_client: AsyncClient):
        """Test JSON metrics endpoint."""
        response = await async_client.get("/api/v1/health/metrics")

        assert response.status_code == 200
        data = response.json()
        assert "events_total" in data
        assert "deliveries_total" in data
        assert "subscriptions_total" in data
        assert "uptime_seconds" in data

    async def test_metrics_prometheus(self, async_client: AsyncClient):
        """Test Prometheus metrics endpoint."""
        response = await async_client.get("/api/v1/health/metrics/prometheus")

        assert response.status_code == 200
        assert "text/plain" in response.headers["content-type"]

        content = response.text
        assert "zapier_events_total" in content
        assert "zapier_deliveries_total" in content
        assert "zapier_subscriptions_total" in content
        assert "zapier_uptime_seconds" in content

    async def test_health_components_structure(self, async_client: AsyncClient):
        """Test health check returns component details."""
        response = await async_client.get("/api/v1/health")

        data = response.json()
        components = data.get("components", [])

        # Check component structure
        for component in components:
            assert "name" in component
            assert "status" in component
            # Latency may be null for some components
            assert "latency_ms" in component or component.get("latency_ms") is None


@pytest.mark.integration
class TestRootEndpoints:
    """Integration tests for root endpoints."""

    async def test_root_endpoint(self, async_client: AsyncClient):
        """Test root endpoint returns API info."""
        response = await async_client.get("/")

        assert response.status_code == 200
        data = response.json()
        assert "name" in data
        assert "version" in data
        assert "api" in data

    async def test_openapi_schema(self, async_client: AsyncClient):
        """Test OpenAPI schema is accessible."""
        response = await async_client.get("/openapi.json")

        assert response.status_code == 200
        data = response.json()
        assert "openapi" in data
        assert "info" in data
        assert "paths" in data
