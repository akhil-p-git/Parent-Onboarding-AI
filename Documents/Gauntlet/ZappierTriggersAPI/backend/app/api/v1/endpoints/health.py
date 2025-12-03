"""
Health Check & System Endpoints.

Provides health checks, readiness probes, and metrics for monitoring.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, Response
from fastapi.responses import PlainTextResponse

from app.api.deps import DBSession
from app.schemas.health import (
    HealthResponse,
    HealthStatus,
    LivenessResponse,
    MetricsResponse,
    ReadinessResponse,
    SystemInfoResponse,
)
from app.services.health_service import HealthService

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_health_service(db: DBSession) -> HealthService:
    """Get health service instance."""
    return HealthService(db)


HealthServiceDep = Annotated[HealthService, Depends(get_health_service)]


@router.get(
    "",
    response_model=HealthResponse,
    summary="Health Check",
    description="Comprehensive health check of all system components.",
    responses={
        200: {"description": "System is healthy"},
        503: {"description": "System is degraded or unhealthy"},
    },
)
async def health_check(
    service: HealthServiceDep,
    response: Response,
) -> HealthResponse:
    """
    Comprehensive health check.

    Returns the health status of the API and all its dependencies:
    - Database connectivity and latency
    - Redis connectivity and latency
    - Queue depth and status

    Returns HTTP 200 if healthy, 503 if degraded or unhealthy.
    """
    health = await service.check_health()

    if health.status != HealthStatus.HEALTHY:
        response.status_code = 503

    return health


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    summary="Readiness Probe",
    description="Check if the service is ready to accept traffic.",
    responses={
        200: {"description": "Service is ready"},
        503: {"description": "Service is not ready"},
    },
)
async def readiness_check(
    service: HealthServiceDep,
    response: Response,
) -> ReadinessResponse:
    """
    Kubernetes readiness probe.

    Returns 200 if the service is ready to accept traffic.
    Used by load balancers to determine if requests should be routed here.
    """
    readiness = await service.check_readiness()

    if not readiness.ready:
        response.status_code = 503

    return readiness


@router.get(
    "/live",
    response_model=LivenessResponse,
    summary="Liveness Probe",
    description="Check if the service is alive.",
)
async def liveness_check(
    service: HealthServiceDep,
) -> LivenessResponse:
    """
    Kubernetes liveness probe.

    Returns 200 if the service process is running.
    If this fails, the container should be restarted.
    """
    return await service.check_liveness()


@router.get(
    "/info",
    response_model=SystemInfoResponse,
    summary="System Information",
    description="Get system and application information.",
)
async def system_info(
    service: HealthServiceDep,
) -> SystemInfoResponse:
    """
    Get system information.

    Returns application name, version, environment, and runtime information.
    """
    return await service.get_system_info()


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="Application Metrics (JSON)",
    description="Get application metrics in JSON format.",
)
async def metrics_json(
    service: HealthServiceDep,
) -> MetricsResponse:
    """
    Get application metrics in JSON format.

    Returns counts of events, deliveries, subscriptions, and queue status.
    """
    return await service.get_metrics()


@router.get(
    "/metrics/prometheus",
    response_class=PlainTextResponse,
    summary="Prometheus Metrics",
    description="Get application metrics in Prometheus format.",
)
async def metrics_prometheus(
    service: HealthServiceDep,
) -> PlainTextResponse:
    """
    Get metrics in Prometheus format.

    Returns metrics in the Prometheus text exposition format
    for scraping by Prometheus server.
    """
    metrics = await service.get_prometheus_metrics()
    return PlainTextResponse(
        content=metrics,
        media_type="text/plain; version=0.0.4; charset=utf-8",
    )
