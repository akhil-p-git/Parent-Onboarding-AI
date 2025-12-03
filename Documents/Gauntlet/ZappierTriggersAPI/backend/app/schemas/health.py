"""
Health Check Schemas.

Pydantic models for health check responses.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import Field

from app.schemas.base import BaseSchema


class HealthStatus(str, Enum):
    """Health status values."""

    HEALTHY = "healthy"
    DEGRADED = "degraded"
    UNHEALTHY = "unhealthy"


class ComponentHealth(BaseSchema):
    """Health status for a single component."""

    name: str = Field(..., description="Component name")
    status: HealthStatus = Field(..., description="Health status")
    latency_ms: float | None = Field(None, description="Response latency in milliseconds")
    message: str | None = Field(None, description="Additional status message")
    details: dict[str, Any] | None = Field(None, description="Component-specific details")


class HealthResponse(BaseSchema):
    """Health check response."""

    status: HealthStatus = Field(..., description="Overall health status")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Current environment")
    timestamp: datetime = Field(..., description="Check timestamp")
    uptime_seconds: float = Field(..., description="Application uptime in seconds")
    components: list[ComponentHealth] = Field(
        default_factory=list,
        description="Individual component health status",
    )


class ReadinessResponse(BaseSchema):
    """Readiness probe response."""

    ready: bool = Field(..., description="Whether the service is ready")
    checks: dict[str, bool] = Field(
        default_factory=dict,
        description="Individual readiness checks",
    )


class LivenessResponse(BaseSchema):
    """Liveness probe response."""

    alive: bool = Field(True, description="Whether the service is alive")
    timestamp: datetime = Field(..., description="Check timestamp")


class SystemInfoResponse(BaseSchema):
    """System information response."""

    app_name: str = Field(..., description="Application name")
    version: str = Field(..., description="Application version")
    environment: str = Field(..., description="Current environment")
    python_version: str = Field(..., description="Python version")
    uptime_seconds: float = Field(..., description="Application uptime")
    timestamp: datetime = Field(..., description="Current timestamp")


class MetricsResponse(BaseSchema):
    """Application metrics response."""

    # Event metrics
    events_total: int = Field(0, description="Total events ingested")
    events_pending: int = Field(0, description="Events pending processing")
    events_delivered: int = Field(0, description="Events successfully delivered")
    events_failed: int = Field(0, description="Events that failed delivery")

    # Delivery metrics
    deliveries_total: int = Field(0, description="Total delivery attempts")
    deliveries_successful: int = Field(0, description="Successful deliveries")
    deliveries_failed: int = Field(0, description="Failed deliveries")
    deliveries_in_flight: int = Field(0, description="Currently processing")

    # Subscription metrics
    subscriptions_total: int = Field(0, description="Total subscriptions")
    subscriptions_active: int = Field(0, description="Active subscriptions")
    subscriptions_healthy: int = Field(0, description="Healthy subscriptions")

    # Queue metrics
    queue_depth: int = Field(0, description="Current queue depth")
    queue_oldest_age_seconds: float | None = Field(
        None, description="Age of oldest item in queue"
    )

    # System metrics
    uptime_seconds: float = Field(..., description="Application uptime")
    timestamp: datetime = Field(..., description="Metrics timestamp")
