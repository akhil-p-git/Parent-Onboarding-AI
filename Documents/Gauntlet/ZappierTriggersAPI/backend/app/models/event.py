"""
Event Model.

Stores inbound events received via the API for processing and delivery.
"""

from datetime import datetime
from enum import Enum
from typing import Any

from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.utils import generate_prefixed_id
from app.models.base import Base, TimestampMixin


class EventStatus(str, Enum):
    """Event processing status."""

    PENDING = "pending"  # Received, awaiting processing
    PROCESSING = "processing"  # Currently being delivered
    DELIVERED = "delivered"  # Successfully delivered to all subscribers
    PARTIALLY_DELIVERED = "partially_delivered"  # Some deliveries failed
    FAILED = "failed"  # All delivery attempts failed
    EXPIRED = "expired"  # Event TTL exceeded


class Event(Base, TimestampMixin):
    """
    Event model for storing inbound webhook events.

    Events are:
    - Received via POST /events
    - Stored with a unique prefixed ID (evt_*)
    - Matched against subscriptions
    - Delivered to subscribers via webhooks
    """

    __tablename__ = "events"

    # Primary key with prefix
    id: Mapped[str] = mapped_column(
        String(32),
        primary_key=True,
        default=lambda: generate_prefixed_id("evt"),
    )

    # Event identification
    event_type: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Event type for filtering (e.g., 'user.created', 'order.completed')",
    )
    source: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        index=True,
        comment="Event source identifier (e.g., 'billing-service', 'auth-service')",
    )

    # Event payload
    data: Mapped[dict[str, Any]] = mapped_column(
        JSONB,
        nullable=False,
        default=dict,
        comment="Event payload data",
    )

    # Optional metadata (using event_meta to avoid SQLAlchemy reserved 'metadata' name)
    event_meta: Mapped[dict[str, Any] | None] = mapped_column(
        "metadata",  # Keep column name as 'metadata' in database
        JSONB,
        nullable=True,
        comment="Additional metadata (correlation_id, trace_id, etc.)",
    )

    # Processing status
    status: Mapped[EventStatus] = mapped_column(
        String(32),
        nullable=False,
        default=EventStatus.PENDING,
        index=True,
    )

    # Idempotency support
    idempotency_key: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
        comment="Client-provided idempotency key for deduplication",
    )

    # API key that created this event
    api_key_id: Mapped[str | None] = mapped_column(
        String(32),
        nullable=True,
        index=True,
        comment="ID of the API key used to create this event",
    )

    # Timestamps for lifecycle tracking
    processed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the event finished processing",
    )
    expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="When the event expires and should no longer be delivered",
    )

    # Delivery tracking
    delivery_attempts: Mapped[int] = mapped_column(
        default=0,
        comment="Number of delivery attempts made",
    )
    successful_deliveries: Mapped[int] = mapped_column(
        default=0,
        comment="Number of successful deliveries",
    )
    failed_deliveries: Mapped[int] = mapped_column(
        default=0,
        comment="Number of failed deliveries",
    )

    # Error information
    last_error: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        comment="Last error message if processing failed",
    )

    # Relationships
    deliveries: Mapped[list["EventDelivery"]] = relationship(
        "EventDelivery",
        back_populates="event",
        cascade="all, delete-orphan",
        lazy="selectin",
    )

    # Indexes for efficient querying
    __table_args__ = (
        Index("ix_events_type_source", "event_type", "source"),
        Index("ix_events_status_created", "status", "created_at"),
        Index("ix_events_created_at_desc", "created_at", postgresql_using="btree"),
        Index(
            "ix_events_data_gin",
            "data",
            postgresql_using="gin",
            postgresql_ops={"data": "jsonb_path_ops"},
        ),
    )

    def __repr__(self) -> str:
        return f"<Event(id={self.id}, type={self.event_type}, status={self.status})>"

    @property
    def is_processed(self) -> bool:
        """Check if event has been processed."""
        return self.status in (
            EventStatus.DELIVERED,
            EventStatus.PARTIALLY_DELIVERED,
            EventStatus.FAILED,
            EventStatus.EXPIRED,
        )

    @property
    def can_retry(self) -> bool:
        """Check if event can be retried."""
        return self.status in (EventStatus.PENDING, EventStatus.PROCESSING)


# Forward reference for relationship
from app.models.event_delivery import EventDelivery  # noqa: E402, F401
