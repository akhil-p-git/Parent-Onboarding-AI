"""
Delivery Service.

Handles webhook delivery execution with retries and tracking.
"""

import hashlib
import hmac
import json
import logging
import time
from datetime import datetime, timedelta, timezone
from typing import Any

import httpx
from sqlalchemy import and_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.utils import generate_prefixed_id, utc_now
from app.models import (
    DeliveryStatus,
    Event,
    EventDelivery,
    EventStatus,
    Subscription,
    SubscriptionStatus,
)

logger = logging.getLogger(__name__)


class DeliveryService:
    """Service for webhook delivery operations."""

    # Default timeout for webhook requests
    DEFAULT_TIMEOUT = 30

    # Maximum response body size to store
    MAX_RESPONSE_BODY_SIZE = 10000

    def __init__(self, db: AsyncSession):
        """Initialize with database session."""
        self.db = db

    async def create_deliveries_for_event(self, event: Event) -> list[EventDelivery]:
        """
        Create delivery records for an event.

        Finds all matching subscriptions and creates delivery records.

        Args:
            event: The event to deliver

        Returns:
            list: Created delivery records
        """
        # Find matching subscriptions
        subscriptions = await self._get_matching_subscriptions(event)

        if not subscriptions:
            logger.info(f"No matching subscriptions for event {event.id}")
            # Update event status
            event.status = EventStatus.DELIVERED
            event.processed_at = utc_now()
            await self.db.flush()
            return []

        deliveries = []
        for subscription in subscriptions:
            delivery = EventDelivery(
                id=generate_prefixed_id("del"),
                event_id=event.id,
                subscription_id=subscription.id,
                status=DeliveryStatus.PENDING,
                max_attempts=subscription.max_retries + 1,  # Initial attempt + retries
                scheduled_at=utc_now(),
                request_url=subscription.target_url,
            )
            self.db.add(delivery)
            deliveries.append(delivery)

        # Update event status
        event.status = EventStatus.PROCESSING
        event.delivery_attempts = len(deliveries)

        await self.db.flush()

        logger.info(
            f"Created {len(deliveries)} deliveries for event {event.id}"
        )

        return deliveries

    async def execute_delivery(self, delivery: EventDelivery) -> bool:
        """
        Execute a single webhook delivery.

        Args:
            delivery: The delivery to execute

        Returns:
            bool: Whether delivery was successful
        """
        # Load related objects
        event = await self.db.get(Event, delivery.event_id)
        subscription = await self.db.get(Subscription, delivery.subscription_id)

        if not event or not subscription:
            logger.error(f"Missing event or subscription for delivery {delivery.id}")
            delivery.status = DeliveryStatus.CANCELLED
            delivery.error_message = "Event or subscription not found"
            await self.db.flush()
            return False

        # Check if subscription is still active
        if subscription.status != SubscriptionStatus.ACTIVE:
            logger.info(f"Subscription {subscription.id} not active, cancelling delivery")
            delivery.status = DeliveryStatus.CANCELLED
            delivery.error_message = f"Subscription status: {subscription.status}"
            await self.db.flush()
            return False

        # Build the webhook payload
        payload = self._build_payload(event)
        payload_json = json.dumps(payload, default=str)

        # Generate signature
        timestamp = int(time.time())
        signature = self._generate_signature(
            payload_json,
            subscription.signing_secret,
            timestamp,
        )

        # Build headers
        headers = self._build_headers(subscription, signature, timestamp)

        # Update delivery status
        delivery.status = DeliveryStatus.IN_FLIGHT
        delivery.started_at = utc_now()
        delivery.attempt_count += 1
        delivery.request_body = payload_json
        delivery.request_headers = {k: v for k, v in headers.items() if "secret" not in k.lower()}
        delivery.signature = signature

        await self.db.flush()

        # Execute the HTTP request
        success = False
        start_time = time.time()

        try:
            async with httpx.AsyncClient(
                timeout=subscription.timeout_seconds or self.DEFAULT_TIMEOUT
            ) as client:
                response = await client.post(
                    subscription.target_url,
                    content=payload_json,
                    headers=headers,
                )

            elapsed_ms = int((time.time() - start_time) * 1000)

            # Record response
            delivery.response_status_code = response.status_code
            delivery.response_time_ms = elapsed_ms
            delivery.response_headers = dict(response.headers)
            delivery.response_body = response.text[:self.MAX_RESPONSE_BODY_SIZE] if response.text else None

            # Check if successful (2xx status)
            if 200 <= response.status_code < 300:
                success = True
                delivery.status = DeliveryStatus.DELIVERED
                delivery.completed_at = utc_now()

                # Update subscription stats
                subscription.record_success()

                logger.info(
                    f"Delivery {delivery.id} succeeded: {response.status_code} in {elapsed_ms}ms"
                )
            else:
                delivery.error_type = "http_error"
                delivery.error_message = f"HTTP {response.status_code}"

                logger.warning(
                    f"Delivery {delivery.id} failed: HTTP {response.status_code}"
                )

        except httpx.TimeoutException:
            elapsed_ms = int((time.time() - start_time) * 1000)
            delivery.response_time_ms = elapsed_ms
            delivery.error_type = "timeout"
            delivery.error_message = f"Request timed out after {subscription.timeout_seconds}s"

            logger.warning(f"Delivery {delivery.id} timed out")

        except httpx.ConnectError as e:
            delivery.error_type = "connection_error"
            delivery.error_message = f"Connection failed: {str(e)}"

            logger.warning(f"Delivery {delivery.id} connection error: {e}")

        except Exception as e:
            delivery.error_type = "unknown_error"
            delivery.error_message = str(e)

            logger.error(f"Delivery {delivery.id} unexpected error: {e}")

        # Handle failure
        if not success:
            await self._handle_delivery_failure(delivery, subscription)

        # Record attempt in history
        self._record_attempt(delivery)

        await self.db.flush()

        return success

    async def get_pending_deliveries(
        self,
        limit: int = 100,
    ) -> list[EventDelivery]:
        """
        Get deliveries ready for processing.

        Args:
            limit: Maximum deliveries to return

        Returns:
            list: Pending delivery records
        """
        now = utc_now()

        result = await self.db.execute(
            select(EventDelivery)
            .where(
                and_(
                    EventDelivery.status.in_([
                        DeliveryStatus.PENDING,
                        DeliveryStatus.RETRYING,
                    ]),
                    EventDelivery.scheduled_at <= now,
                )
            )
            .order_by(EventDelivery.scheduled_at.asc())
            .limit(limit)
        )

        return list(result.scalars().all())

    async def retry_delivery(self, delivery: EventDelivery) -> None:
        """
        Schedule a delivery for retry.

        Args:
            delivery: The delivery to retry
        """
        subscription = await self.db.get(Subscription, delivery.subscription_id)
        if not subscription:
            return

        # Calculate retry delay
        delay = subscription.calculate_retry_delay(delivery.attempt_count)

        delivery.status = DeliveryStatus.RETRYING
        delivery.next_retry_at = utc_now() + timedelta(seconds=delay)
        delivery.scheduled_at = delivery.next_retry_at
        delivery.retry_delay_seconds = delay

        logger.info(
            f"Scheduled delivery {delivery.id} for retry in {delay}s "
            f"(attempt {delivery.attempt_count + 1}/{delivery.max_attempts})"
        )

    async def move_to_dlq(self, delivery: EventDelivery) -> None:
        """
        Move a delivery to the dead letter queue.

        Args:
            delivery: The exhausted delivery
        """
        delivery.status = DeliveryStatus.EXHAUSTED
        delivery.completed_at = utc_now()

        # Update event status
        event = await self.db.get(Event, delivery.event_id)
        if event:
            event.failed_deliveries += 1
            event.last_error = delivery.error_message

            # Check if all deliveries for this event have completed
            await self._update_event_status(event)

        # Update subscription stats
        subscription = await self.db.get(Subscription, delivery.subscription_id)
        if subscription:
            subscription.record_failure(delivery.error_message or "Max retries exceeded")

        logger.warning(
            f"Delivery {delivery.id} moved to DLQ after {delivery.attempt_count} attempts"
        )

    async def _get_matching_subscriptions(self, event: Event) -> list[Subscription]:
        """Get active subscriptions matching an event."""
        result = await self.db.execute(
            select(Subscription).where(
                and_(
                    Subscription.status == SubscriptionStatus.ACTIVE,
                    Subscription.is_healthy == True,
                    Subscription.deleted_at.is_(None),
                )
            )
        )

        subscriptions = list(result.scalars().all())

        # Filter by event type and source
        return [
            sub for sub in subscriptions
            if sub.matches_event(event.event_type, event.source)
        ]

    async def _handle_delivery_failure(
        self,
        delivery: EventDelivery,
        subscription: Subscription,
    ) -> None:
        """Handle a failed delivery attempt."""
        if delivery.attempt_count < delivery.max_attempts:
            # Schedule retry
            await self.retry_delivery(delivery)
        else:
            # Move to DLQ
            await self.move_to_dlq(delivery)

    async def _update_event_status(self, event: Event) -> None:
        """Update event status based on delivery results."""
        # Count delivery statuses
        result = await self.db.execute(
            select(EventDelivery.status)
            .where(EventDelivery.event_id == event.id)
        )
        statuses = [row[0] for row in result]

        if not statuses:
            return

        delivered = sum(1 for s in statuses if s == DeliveryStatus.DELIVERED)
        failed = sum(1 for s in statuses if s == DeliveryStatus.EXHAUSTED)
        pending = sum(1 for s in statuses if s in [
            DeliveryStatus.PENDING,
            DeliveryStatus.RETRYING,
            DeliveryStatus.IN_FLIGHT,
        ])

        event.successful_deliveries = delivered
        event.failed_deliveries = failed

        if pending > 0:
            event.status = EventStatus.PROCESSING
        elif delivered > 0 and failed == 0:
            event.status = EventStatus.DELIVERED
            event.processed_at = utc_now()
        elif delivered > 0 and failed > 0:
            event.status = EventStatus.PARTIALLY_DELIVERED
            event.processed_at = utc_now()
        elif failed > 0 and delivered == 0:
            event.status = EventStatus.FAILED
            event.processed_at = utc_now()

    def _build_payload(self, event: Event) -> dict[str, Any]:
        """Build the webhook payload."""
        return {
            "id": event.id,
            "event_type": event.event_type,
            "source": event.source,
            "data": event.data,
            "metadata": event.event_meta,
            "created_at": event.created_at.isoformat() if event.created_at else None,
        }

    def _generate_signature(
        self,
        payload: str,
        secret: str,
        timestamp: int,
    ) -> str:
        """
        Generate HMAC-SHA256 signature for webhook payload.

        Format: v1=<signature>
        Signed message: <timestamp>.<payload>
        """
        message = f"{timestamp}.{payload}"
        signature = hmac.new(
            secret.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()

        return f"v1={signature}"

    def _build_headers(
        self,
        subscription: Subscription,
        signature: str,
        timestamp: int,
    ) -> dict[str, str]:
        """Build headers for webhook request."""
        headers = {
            "Content-Type": "application/json",
            "User-Agent": f"Zapier-Webhooks/{settings.APP_VERSION}",
            "X-Webhook-Signature": signature,
            "X-Webhook-Timestamp": str(timestamp),
            "X-Webhook-ID": subscription.id,
        }

        # Add custom headers
        if subscription.custom_headers:
            headers.update(subscription.custom_headers)

        return headers

    def _record_attempt(self, delivery: EventDelivery) -> None:
        """Record delivery attempt in history."""
        attempt = {
            "attempt": delivery.attempt_count,
            "timestamp": utc_now().isoformat(),
            "status_code": delivery.response_status_code,
            "response_time_ms": delivery.response_time_ms,
            "error_type": delivery.error_type,
            "error_message": delivery.error_message,
        }

        if delivery.attempt_history is None:
            delivery.attempt_history = []

        delivery.attempt_history.append(attempt)
