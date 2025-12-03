"""
Event Delivery Model.

Tracks individual delivery attempts for events to subscriptions.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.utils import generate_prefixed_id
from app.models.base import Base, TimestampMixin


class DeliveryStatus(str, Enum):
    """Delivery attempt status."""

    PENDING = "pending"  # Awaiting delivery
    IN_FLIGHT = "in_flight"  # Currently being delivered
    DELIVERED = "delivered"  # Successfully delivered
    FAILED = "failed"  # Delivery failed (may retry)
    RETRYING = "retrying"  # Scheduled for retry
    EXHAUSTED = "exhausted"  # All retries exhausted
    CANCELLED = "cancelled"  # Manually cancelled


class EventDelivery(Base, TimestampMixin):
    """
    Event Delivery model for tracking webhook delivery attempts.

    Each delivery record represents:
    - A single event being delivered to a single subscription
    - Multiple attempts may occur (retries)
    - Full audit trail of delivery attempts
    """

    __tablename__ = "event_deliveries"

    # Primary key with prefix
    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=lambda: generate_prefixed_id("del"),
    )

    # Foreign keys
    event_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("events.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    subscription_id: Mapped[str] = mapped_column(
        String(32),
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Delivery status
    status: Mapped[DeliveryStatus] = mapped_column(
        String(32),
        nullable=False,
        default=DeliveryStatus.PENDING,
        index=True,
    )

    # Attempt tracking
    attempt_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of delivery attempts made",
    )
    max_attempts: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
        comment="Maximum attempts before giving up",
    )

    # Scheduling
    scheduled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="When this delivery is scheduled to run",
    )
    started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the current attempt started",
    )
    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the delivery completed (success or final failure)",
    )

    # Request details
    request_url: Mapped[str | None] = mapped_column(
        String(2048),
        nullable=True,
        comment="Target URL for the webhook request",
    )
    request_headers: Mapped[dict[str, str] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Headers sent with the request",
    )
    request_body: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Request body (JSON payload)",
    )

    # Response details
    response_status_code: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="HTTP status code from the response",
    )
    response_headers: Mapped[dict[str, str] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Headers received in the response",
    )
    response_body: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Response body (truncated if large)",
    )
    response_time_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Response time in milliseconds",
    )

    # Error information
    error_type: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        comment="Type of error (timeout, connection_error, etc.)",
    )
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Detailed error message",
    )

    # Retry information
    next_retry_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        index=True,
        comment="When the next retry is scheduled",
    )
    retry_delay_seconds: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Delay before the next retry",
    )

    # Webhook signature
    signature: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        comment="HMAC signature sent with the webhook",
    )
    signature_header: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default="X-Webhook-Signature",
        comment="Header name for the signature",
    )

    # Metadata (using delivery_meta to avoid SQLAlchemy reserved 'metadata' name)
    delivery_meta: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",  # Keep column name as 'metadata' in database
        JSONB,
        nullable=True,
        comment="Additional metadata (worker_id, trace_id, etc.)",
    )

    # Attempt history (array of attempt details)
    attempt_history: Mapped[list[dict[str, Any]] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="History of all delivery attempts",
    )

    # Relationships
    event: Mapped["Event"] = relationship(
        "Event",
        back_populates="deliveries",
    )
    subscription: Mapped["Subscription"] = relationship(
        "Subscription",
        back_populates="deliveries",
    )

    # Indexes for efficient querying
    __table_args__ = (
        Index("ix_deliveries_status_scheduled", "status", "scheduled_at"),
        Index("ix_deliveries_event_subscription", "event_id", "subscription_id"),
        Index("ix_deliveries_retry", "status", "next_retry_at"),
        Index(
            "ix_deliveries_pending_scheduled",
            "status",
            "scheduled_at",
            postgresql_where="status IN ('pending', 'retrying')",
        ),
    )

    def __repr__(self) -> str:
        return f"<EventDelivery(id={self.id}, event={self.event_id}, status={self.status})>"

    @property
    def is_complete(self) -> bool:
        """Check if delivery is in a terminal state."""
        return self.status in (
            DeliveryStatus.DELIVERED,
            DeliveryStatus.EXHAUSTED,
            DeliveryStatus.CANCELLED,
        )

    @property
    def can_retry(self) -> bool:
        """Check if delivery can be retried."""
        if self.is_complete:
            return False
        return self.attempt_count < self.max_attempts

    @property
    def is_success(self) -> bool:
        """Check if delivery was successful."""
        return self.status == DeliveryStatus.DELIVERED

    def record_attempt(
        self,
        status_code: int | None = None,
        response_time_ms: int | None = None,
        error_type: str | None = None,
        error_message: str | None = None,
        response_body: str | None = None,
    ) -> None:
        """Record a delivery attempt."""
        from app.core.utils import utc_now

        self.attempt_count += 1

        # Build attempt record
        attempt_record = {
            "attempt": self.attempt_count,
            "timestamp": utc_now().isoformat(),
            "status_code": status_code,
            "response_time_ms": response_time_ms,
            "error_type": error_type,
            "error_message": error_message,
        }

        # Update attempt history
        if self.attempt_history is None:
            self.attempt_history = []
        self.attempt_history.append(attempt_record)

        # Update response fields
        self.response_status_code = status_code
        self.response_time_ms = response_time_ms
        self.response_body = response_body[:10000] if response_body else None
        self.error_type = error_type
        self.error_message = error_message

        # Determine if successful (2xx status)
        if status_code and 200 <= status_code < 300:
            self.status = DeliveryStatus.DELIVERED
            self.completed_at = utc_now()
        elif not self.can_retry:
            self.status = DeliveryStatus.EXHAUSTED
            self.completed_at = utc_now()
        else:
            self.status = DeliveryStatus.RETRYING


# Forward references for relationships
from app.models.event import Event  # noqa: E402, F401
from app.models.subscription import Subscription  # noqa: E402, F401
