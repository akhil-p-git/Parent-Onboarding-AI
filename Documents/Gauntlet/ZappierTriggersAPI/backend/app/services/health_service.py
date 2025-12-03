"""
Health Service.

Provides health checks and metrics for system monitoring.
"""

import logging
import sys
import time
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.redis import get_redis
from app.models import (
    DeliveryStatus,
    Event,
    EventDelivery,
    EventStatus,
    Subscription,
    SubscriptionStatus,
)
from app.schemas.health import (
    ComponentHealth,
    HealthResponse,
    HealthStatus,
    LivenessResponse,
    MetricsResponse,
    ReadinessResponse,
    SystemInfoResponse,
)

logger = logging.getLogger(__name__)

# Track application start time
_start_time: float = time.time()


def get_uptime() -> float:
    """Get application uptime in seconds."""
    return time.time() - _start_time


class HealthService:
    """Service for health checks and metrics."""

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db

    async def check_health(self) -> HealthResponse:
        """
        Perform comprehensive health check.

        Returns:
            HealthResponse: Overall health status with component details
        """
        components = []
        overall_status = HealthStatus.HEALTHY

        # Check database
        db_health = await self._check_database()
        components.append(db_health)
        if db_health.status != HealthStatus.HEALTHY:
            overall_status = HealthStatus.DEGRADED

        # Check Redis
        redis_health = await self._check_redis()
        components.append(redis_health)
        if redis_health.status != HealthStatus.HEALTHY:
            overall_status = HealthStatus.DEGRADED

        # Check queue health
        queue_health = await self._check_queue()
        components.append(queue_health)
        if queue_health.status == HealthStatus.UNHEALTHY:
            overall_status = HealthStatus.DEGRADED

        return HealthResponse(
            status=overall_status,
            version=settings.APP_VERSION,
            environment=settings.APP_ENV,
            timestamp=datetime.now(timezone.utc),
            uptime_seconds=get_uptime(),
            components=components,
        )

    async def check_readiness(self) -> ReadinessResponse:
        """
        Check if service is ready to accept traffic.

        Returns:
            ReadinessResponse: Readiness status
        """
        checks = {}

        # Database must be available
        try:
            await self.db.execute(text("SELECT 1"))
            checks["database"] = True
        except Exception:
            checks["database"] = False

        # Redis should be available (but not required)
        try:
            redis = await get_redis()
            await redis.ping()
            checks["redis"] = True
        except Exception:
            checks["redis"] = False

        # Ready if database is available
        ready = checks.get("database", False)

        return ReadinessResponse(ready=ready, checks=checks)

    async def check_liveness(self) -> LivenessResponse:
        """
        Check if service is alive.

        Returns:
            LivenessResponse: Liveness status
        """
        return LivenessResponse(
            alive=True,
            timestamp=datetime.now(timezone.utc),
        )

    async def get_system_info(self) -> SystemInfoResponse:
        """
        Get system information.

        Returns:
            SystemInfoResponse: System information
        """
        return SystemInfoResponse(
            app_name=settings.APP_NAME,
            version=settings.APP_VERSION,
            environment=settings.APP_ENV,
            python_version=sys.version,
            uptime_seconds=get_uptime(),
            timestamp=datetime.now(timezone.utc),
        )

    async def get_metrics(self) -> MetricsResponse:
        """
        Get application metrics.

        Returns:
            MetricsResponse: Application metrics
        """
        # Event metrics
        event_stats = await self._get_event_stats()

        # Delivery metrics
        delivery_stats = await self._get_delivery_stats()

        # Subscription metrics
        subscription_stats = await self._get_subscription_stats()

        # Queue metrics
        queue_stats = await self._get_queue_stats()

        return MetricsResponse(
            events_total=event_stats.get("total", 0),
            events_pending=event_stats.get("pending", 0),
            events_delivered=event_stats.get("delivered", 0),
            events_failed=event_stats.get("failed", 0),
            deliveries_total=delivery_stats.get("total", 0),
            deliveries_successful=delivery_stats.get("successful", 0),
            deliveries_failed=delivery_stats.get("failed", 0),
            deliveries_in_flight=delivery_stats.get("in_flight", 0),
            subscriptions_total=subscription_stats.get("total", 0),
            subscriptions_active=subscription_stats.get("active", 0),
            subscriptions_healthy=subscription_stats.get("healthy", 0),
            queue_depth=queue_stats.get("depth", 0),
            queue_oldest_age_seconds=queue_stats.get("oldest_age"),
            uptime_seconds=get_uptime(),
            timestamp=datetime.now(timezone.utc),
        )

    async def get_prometheus_metrics(self) -> str:
        """
        Get metrics in Prometheus format.

        Returns:
            str: Prometheus-formatted metrics
        """
        metrics = await self.get_metrics()
        lines = []

        # Help and type definitions
        lines.append("# HELP zapier_events_total Total number of events ingested")
        lines.append("# TYPE zapier_events_total counter")
        lines.append(f"zapier_events_total {metrics.events_total}")

        lines.append("# HELP zapier_events_pending Number of events pending processing")
        lines.append("# TYPE zapier_events_pending gauge")
        lines.append(f"zapier_events_pending {metrics.events_pending}")

        lines.append("# HELP zapier_events_delivered Number of events delivered")
        lines.append("# TYPE zapier_events_delivered counter")
        lines.append(f"zapier_events_delivered {metrics.events_delivered}")

        lines.append("# HELP zapier_events_failed Number of events that failed")
        lines.append("# TYPE zapier_events_failed counter")
        lines.append(f"zapier_events_failed {metrics.events_failed}")

        lines.append("# HELP zapier_deliveries_total Total delivery attempts")
        lines.append("# TYPE zapier_deliveries_total counter")
        lines.append(f"zapier_deliveries_total {metrics.deliveries_total}")

        lines.append("# HELP zapier_deliveries_successful Successful deliveries")
        lines.append("# TYPE zapier_deliveries_successful counter")
        lines.append(f"zapier_deliveries_successful {metrics.deliveries_successful}")

        lines.append("# HELP zapier_deliveries_failed Failed deliveries")
        lines.append("# TYPE zapier_deliveries_failed counter")
        lines.append(f"zapier_deliveries_failed {metrics.deliveries_failed}")

        lines.append("# HELP zapier_deliveries_in_flight Deliveries currently in flight")
        lines.append("# TYPE zapier_deliveries_in_flight gauge")
        lines.append(f"zapier_deliveries_in_flight {metrics.deliveries_in_flight}")

        lines.append("# HELP zapier_subscriptions_total Total subscriptions")
        lines.append("# TYPE zapier_subscriptions_total gauge")
        lines.append(f"zapier_subscriptions_total {metrics.subscriptions_total}")

        lines.append("# HELP zapier_subscriptions_active Active subscriptions")
        lines.append("# TYPE zapier_subscriptions_active gauge")
        lines.append(f"zapier_subscriptions_active {metrics.subscriptions_active}")

        lines.append("# HELP zapier_subscriptions_healthy Healthy subscriptions")
        lines.append("# TYPE zapier_subscriptions_healthy gauge")
        lines.append(f"zapier_subscriptions_healthy {metrics.subscriptions_healthy}")

        lines.append("# HELP zapier_queue_depth Current queue depth")
        lines.append("# TYPE zapier_queue_depth gauge")
        lines.append(f"zapier_queue_depth {metrics.queue_depth}")

        lines.append("# HELP zapier_uptime_seconds Application uptime in seconds")
        lines.append("# TYPE zapier_uptime_seconds gauge")
        lines.append(f"zapier_uptime_seconds {metrics.uptime_seconds}")

        return "\n".join(lines) + "\n"

    async def _check_database(self) -> ComponentHealth:
        """Check database health with latency measurement."""
        start = time.time()
        try:
            await self.db.execute(text("SELECT 1"))
            latency_ms = (time.time() - start) * 1000

            # Check if latency is acceptable
            if latency_ms > 1000:  # 1 second threshold
                return ComponentHealth(
                    name="database",
                    status=HealthStatus.DEGRADED,
                    latency_ms=latency_ms,
                    message="High latency detected",
                )

            return ComponentHealth(
                name="database",
                status=HealthStatus.HEALTHY,
                latency_ms=latency_ms,
            )

        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            return ComponentHealth(
                name="database",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                message=str(e),
            )

    async def _check_redis(self) -> ComponentHealth:
        """Check Redis health with latency measurement."""
        start = time.time()
        try:
            redis = await get_redis()
            await redis.ping()
            latency_ms = (time.time() - start) * 1000

            # Get additional Redis info
            info = await redis.info("server")
            details = {
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
            }

            if latency_ms > 100:  # 100ms threshold for Redis
                return ComponentHealth(
                    name="redis",
                    status=HealthStatus.DEGRADED,
                    latency_ms=latency_ms,
                    message="High latency detected",
                    details=details,
                )

            return ComponentHealth(
                name="redis",
                status=HealthStatus.HEALTHY,
                latency_ms=latency_ms,
                details=details,
            )

        except Exception as e:
            latency_ms = (time.time() - start) * 1000
            return ComponentHealth(
                name="redis",
                status=HealthStatus.UNHEALTHY,
                latency_ms=latency_ms,
                message=str(e),
            )

    async def _check_queue(self) -> ComponentHealth:
        """Check queue health."""
        try:
            redis = await get_redis()

            # Check queue depth
            queue_key = "events:pending"
            depth = await redis.llen(queue_key)

            # Check DLQ depth
            dlq_key = "events:dlq"
            dlq_depth = await redis.llen(dlq_key)

            details = {
                "queue_depth": depth,
                "dlq_depth": dlq_depth,
            }

            # High queue depth indicates backlog
            if depth > 10000:
                return ComponentHealth(
                    name="queue",
                    status=HealthStatus.DEGRADED,
                    message=f"High queue depth: {depth}",
                    details=details,
                )

            # High DLQ indicates delivery problems
            if dlq_depth > 1000:
                return ComponentHealth(
                    name="queue",
                    status=HealthStatus.DEGRADED,
                    message=f"High DLQ depth: {dlq_depth}",
                    details=details,
                )

            return ComponentHealth(
                name="queue",
                status=HealthStatus.HEALTHY,
                details=details,
            )

        except Exception as e:
            return ComponentHealth(
                name="queue",
                status=HealthStatus.UNHEALTHY,
                message=str(e),
            )

    async def _get_event_stats(self) -> dict[str, int]:
        """Get event statistics from database."""
        try:
            result = await self.db.execute(
                select(Event.status, func.count(Event.id)).group_by(Event.status)
            )

            stats = {"total": 0, "pending": 0, "delivered": 0, "failed": 0}
            for status, count in result:
                stats["total"] += count
                if status == EventStatus.PENDING:
                    stats["pending"] += count
                elif status == EventStatus.DELIVERED:
                    stats["delivered"] += count
                elif status == EventStatus.FAILED:
                    stats["failed"] += count

            return stats
        except Exception as e:
            logger.warning(f"Failed to get event stats: {e}")
            return {}

    async def _get_delivery_stats(self) -> dict[str, int]:
        """Get delivery statistics from database."""
        try:
            result = await self.db.execute(
                select(EventDelivery.status, func.count(EventDelivery.id)).group_by(
                    EventDelivery.status
                )
            )

            stats = {"total": 0, "successful": 0, "failed": 0, "in_flight": 0}
            for status, count in result:
                stats["total"] += count
                if status == DeliveryStatus.DELIVERED:
                    stats["successful"] += count
                elif status in (DeliveryStatus.EXHAUSTED, DeliveryStatus.CANCELLED):
                    stats["failed"] += count
                elif status == DeliveryStatus.IN_FLIGHT:
                    stats["in_flight"] += count

            return stats
        except Exception as e:
            logger.warning(f"Failed to get delivery stats: {e}")
            return {}

    async def _get_subscription_stats(self) -> dict[str, int]:
        """Get subscription statistics from database."""
        try:
            result = await self.db.execute(
                select(
                    Subscription.status,
                    Subscription.is_healthy,
                    func.count(Subscription.id),
                )
                .where(Subscription.deleted_at.is_(None))
                .group_by(Subscription.status, Subscription.is_healthy)
            )

            stats = {"total": 0, "active": 0, "healthy": 0}
            for status, is_healthy, count in result:
                stats["total"] += count
                if status == SubscriptionStatus.ACTIVE:
                    stats["active"] += count
                if is_healthy:
                    stats["healthy"] += count

            return stats
        except Exception as e:
            logger.warning(f"Failed to get subscription stats: {e}")
            return {}

    async def _get_queue_stats(self) -> dict[str, Any]:
        """Get queue statistics from Redis."""
        try:
            redis = await get_redis()

            depth = await redis.llen("events:pending")

            # Get oldest item age (if any)
            oldest_age = None
            oldest = await redis.lindex("events:pending", -1)
            if oldest:
                import json

                try:
                    data = json.loads(oldest)
                    if "timestamp" in data:
                        oldest_age = time.time() - data["timestamp"]
                except Exception:
                    pass

            return {"depth": depth, "oldest_age": oldest_age}
        except Exception as e:
            logger.warning(f"Failed to get queue stats: {e}")
            return {"depth": 0, "oldest_age": None}
