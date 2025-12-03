"""
Subscription Model.

Manages webhook subscriptions for event delivery.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import Boolean, DateTime, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import ARRAY, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.utils import generate_prefixed_id, generate_signing_secret
from app.models.base import Base, TimestampMixin


class SubscriptionStatus(str, Enum):
    """Subscription status."""

    ACTIVE = "active"  # Receiving events
    PAUSED = "paused"  # Temporarily paused
    DISABLED = "disabled"  # Disabled due to failures
    DELETED = "deleted"  # Soft deleted


class RetryStrategy(str, Enum):
    """Retry strategy for failed deliveries."""

    EXPONENTIAL = "exponential"  # Exponential backoff
    LINEAR = "linear"  # Linear backoff
    FIXED = "fixed"  # Fixed interval


class Subscription(Base, TimestampMixin):
    """
    Subscription model for webhook delivery configuration.

    Subscriptions define:
    - Where to deliver events (target URL)
    - Which events to deliver (filters)
    - How to authenticate (signing secret, headers)
    - Retry policy for failures
    """

    __tablename__ = "subscriptions"

    # Primary key with prefix
    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=lambda: generate_prefixed_id("sub"),
    )

    # Subscription identification
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        comment="Human-readable name for the subscription",
    )
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Optional description",
    )

    # Target configuration
    target_url: Mapped[str] = mapped_column(
        String(2048),
        nullable=False,
        comment="Webhook URL to deliver events to",
    )

    # Authentication
    signing_secret: Mapped[str] = mapped_column(
        String(64),
        nullable=False,
        default=generate_signing_secret,
        comment="HMAC signing secret for webhook signatures",
    )

    # Custom headers for webhook requests
    custom_headers: Mapped[dict[str, str] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Custom headers to include in webhook requests",
    )

    # Event filtering
    event_types: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(255)),
        nullable=True,
        comment="Event types to subscribe to (null = all)",
    )
    event_sources: Mapped[list[str] | None] = mapped_column(
        ARRAY(String(255)),
        nullable=True,
        comment="Event sources to subscribe to (null = all)",
    )

    # Advanced filtering with JSONPath expressions
    filters: Mapped[dict[str, Any] | None] = mapped_column(
        JSONB,
        nullable=True,
        comment="Advanced filter expressions (JSONPath or custom)",
    )

    # Status
    status: Mapped[SubscriptionStatus] = mapped_column(
        String(32),
        nullable=False,
        default=SubscriptionStatus.ACTIVE,
        index=True,
    )

    # Retry configuration
    retry_strategy: Mapped[RetryStrategy] = mapped_column(
        String(32),
        nullable=False,
        default=RetryStrategy.EXPONENTIAL,
    )
    max_retries: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=5,
        comment="Maximum retry attempts",
    )
    retry_delay_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=60,
        comment="Initial retry delay in seconds",
    )
    retry_max_delay_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=3600,
        comment="Maximum retry delay (for exponential backoff)",
    )

    # Timeout configuration
    timeout_seconds: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=30,
        comment="Request timeout in seconds",
    )

    # Rate limiting
    rate_limit: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        comment="Max events per second (null for no limit)",
    )

    # Ownership
    api_key_id: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        index=True,
        comment="API key that created this subscription",
    )

    # Health tracking
    is_healthy: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        index=True,
    )
    consecutive_failures: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        comment="Number of consecutive delivery failures",
    )
    failure_threshold: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=10,
        comment="Failures before auto-disable",
    )
    last_success_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_failure_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    last_failure_reason: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Statistics
    total_deliveries: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    successful_deliveries: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )
    failed_deliveries: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
    )

    # Soft delete
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Metadata (using sub_meta to avoid SQLAlchemy reserved 'metadata' name)
    sub_meta: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",  # Keep column name as 'metadata' in database
        JSONB,
        nullable=True,
    )

    # Relationships
    deliveries: Mapped[list["EventDelivery"]] = relationship(
        "EventDelivery",
        back_populates="subscription",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Indexes
    __table_args__ = (
        Index("ix_subscriptions_status_healthy", "status", "is_healthy"),
        Index("ix_subscriptions_api_key_status", "api_key_id", "status"),
    )

    def __repr__(self) -> str:
        return f"<Subscription(id={self.id}, name={self.name}, status={self.status})>"

    @property
    def is_active(self) -> bool:
        """Check if subscription is active and receiving events."""
        return self.status == SubscriptionStatus.ACTIVE and self.deleted_at is None

    def matches_event(self, event_type: str, event_source: str) -> bool:
        """Check if this subscription should receive an event."""
        if not self.is_active:
            return False

        # Check event type filter
        if self.event_types is not None and event_type not in self.event_types:
            return False

        # Check event source filter
        if self.event_sources is not None and event_source not in self.event_sources:
            return False

        return True

    def record_success(self) -> None:
        """Record a successful delivery."""
        from app.core.utils import utc_now

        self.last_success_at = utc_now()
        self.consecutive_failures = 0
        self.is_healthy = True
        self.total_deliveries += 1
        self.successful_deliveries += 1

    def record_failure(self, reason: str) -> None:
        """Record a failed delivery."""
        from app.core.utils import utc_now

        self.last_failure_at = utc_now()
        self.last_failure_reason = reason
        self.consecutive_failures += 1
        self.total_deliveries += 1
        self.failed_deliveries += 1

        # Auto-disable if threshold exceeded
        if self.consecutive_failures >= self.failure_threshold:
            self.is_healthy = False
            self.status = SubscriptionStatus.DISABLED

    def calculate_retry_delay(self, attempt: int) -> int:
        """Calculate delay for retry attempt."""
        if self.retry_strategy == RetryStrategy.FIXED:
            return self.retry_delay_seconds

        if self.retry_strategy == RetryStrategy.LINEAR:
            delay = self.retry_delay_seconds * attempt
        else:  # EXPONENTIAL
            delay = self.retry_delay_seconds * (2 ** (attempt - 1))

        return min(delay, self.retry_max_delay_seconds)


# Forward reference for relationship
from app.models.event_delivery import EventDelivery  # noqa: E402, F401
