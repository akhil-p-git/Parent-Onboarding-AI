"""
Subscription Schemas.

Request and response schemas for webhook subscription operations.
"""

from datetime import datetime
from typing import Any

from pydantic import Field, HttpUrl, field_validator, model_validator

from app.models.subscription import RetryStrategy, SubscriptionStatus
from app.schemas.base import BaseSchema, PaginationMeta, TimestampMixin


class WebhookConfig(BaseSchema):
    """Webhook delivery configuration."""

    timeout_seconds: int = Field(
        default=30,
        ge=1,
        le=60,
        description="Request timeout in seconds",
    )
    retry_strategy: RetryStrategy = Field(
        default=RetryStrategy.EXPONENTIAL,
        description="Retry strategy for failed deliveries",
    )
    max_retries: int = Field(
        default=5,
        ge=0,
        le=10,
        description="Maximum retry attempts",
    )
    retry_delay_seconds: int = Field(
        default=60,
        ge=1,
        le=3600,
        description="Initial retry delay in seconds",
    )
    retry_max_delay_seconds: int = Field(
        default=3600,
        ge=60,
        le=86400,
        description="Maximum retry delay for exponential backoff",
    )


class EventFilter(BaseSchema):
    """Event filtering configuration for subscription."""

    event_types: list[str] | None = Field(
        default=None,
        description="Event types to subscribe to (null = all)",
        examples=[["user.created", "user.updated"]],
    )
    event_sources: list[str] | None = Field(
        default=None,
        description="Event sources to subscribe to (null = all)",
        examples=[["billing-service"]],
    )
    advanced_filters: dict[str, Any] | None = Field(
        default=None,
        description="Advanced filter expressions (JSONPath)",
        examples=[{"$.data.amount": {"$gt": 100}}],
    )


class CreateSubscriptionRequest(BaseSchema):
    """Request schema for creating a subscription."""

    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Human-readable subscription name",
        examples=["Production Webhook"],
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="Optional description",
    )
    target_url: str = Field(
        ...,
        description="Webhook URL to deliver events to",
        examples=["https://api.example.com/webhooks/zapier"],
    )
    custom_headers: dict[str, str] | None = Field(
        default=None,
        description="Custom headers to include in webhook requests",
        examples=[{"X-Custom-Header": "value"}],
    )
    filters: EventFilter | None = Field(
        default=None,
        description="Event filtering configuration",
    )
    webhook_config: WebhookConfig | None = Field(
        default=None,
        description="Webhook delivery configuration",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional metadata",
    )

    @field_validator("target_url")
    @classmethod
    def validate_target_url(cls, v: str) -> str:
        """Validate target URL."""
        if not v:
            raise ValueError("target_url is required")

        # Must be HTTPS in production (allow HTTP for local development)
        v = v.strip()
        if not v.startswith(("https://", "http://localhost", "http://127.0.0.1")):
            raise ValueError("target_url must use HTTPS (except for localhost)")

        # Basic URL validation
        from urllib.parse import urlparse
        parsed = urlparse(v)
        if not parsed.netloc:
            raise ValueError("Invalid URL format")

        return v

    @field_validator("custom_headers")
    @classmethod
    def validate_custom_headers(cls, v: dict[str, str] | None) -> dict[str, str] | None:
        """Validate custom headers."""
        if v is None:
            return v

        # Prevent overriding critical headers
        forbidden = {
            "content-type",
            "content-length",
            "host",
            "authorization",
            "x-webhook-signature",
            "x-webhook-timestamp",
        }
        for key in v.keys():
            if key.lower() in forbidden:
                raise ValueError(f"Cannot override reserved header: {key}")

        # Limit number of headers
        if len(v) > 20:
            raise ValueError("Maximum 20 custom headers allowed")

        return v


class UpdateSubscriptionRequest(BaseSchema):
    """Request schema for updating a subscription."""

    name: str | None = Field(
        default=None,
        min_length=1,
        max_length=255,
        description="New subscription name",
    )
    description: str | None = Field(
        default=None,
        max_length=1000,
        description="New description",
    )
    target_url: str | None = Field(
        default=None,
        description="New webhook URL",
    )
    custom_headers: dict[str, str] | None = Field(
        default=None,
        description="New custom headers",
    )
    filters: EventFilter | None = Field(
        default=None,
        description="New event filters",
    )
    webhook_config: WebhookConfig | None = Field(
        default=None,
        description="New webhook configuration",
    )
    status: SubscriptionStatus | None = Field(
        default=None,
        description="New status",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="New metadata",
    )

    @model_validator(mode="after")
    def validate_at_least_one_field(self) -> "UpdateSubscriptionRequest":
        """Ensure at least one field is provided for update."""
        fields = [
            self.name,
            self.description,
            self.target_url,
            self.custom_headers,
            self.filters,
            self.webhook_config,
            self.status,
            self.metadata,
        ]
        if all(f is None for f in fields):
            raise ValueError("At least one field must be provided for update")
        return self


class SubscriptionResponse(BaseSchema, TimestampMixin):
    """Response schema for a subscription."""

    id: str = Field(
        ...,
        description="Unique subscription identifier",
        examples=["sub_01ARZ3NDEKTSV4RRFFQ69G5FAV"],
    )
    name: str = Field(
        ...,
        description="Subscription name",
    )
    description: str | None = Field(
        default=None,
        description="Subscription description",
    )
    target_url: str = Field(
        ...,
        description="Webhook URL",
    )
    status: SubscriptionStatus = Field(
        ...,
        description="Subscription status",
    )
    event_types: list[str] | None = Field(
        default=None,
        description="Subscribed event types",
    )
    event_sources: list[str] | None = Field(
        default=None,
        description="Subscribed event sources",
    )
    custom_headers: dict[str, str] | None = Field(
        default=None,
        description="Custom headers (values masked)",
    )
    webhook_config: WebhookConfig = Field(
        ...,
        description="Webhook delivery configuration",
    )
    is_healthy: bool = Field(
        ...,
        description="Whether the subscription is healthy",
    )
    consecutive_failures: int = Field(
        default=0,
        description="Current consecutive failure count",
    )
    last_success_at: datetime | None = Field(
        default=None,
        description="Last successful delivery",
    )
    last_failure_at: datetime | None = Field(
        default=None,
        description="Last failed delivery",
    )
    last_failure_reason: str | None = Field(
        default=None,
        description="Last failure reason",
    )
    total_deliveries: int = Field(
        default=0,
        description="Total delivery attempts",
    )
    successful_deliveries: int = Field(
        default=0,
        description="Successful deliveries",
    )
    failed_deliveries: int = Field(
        default=0,
        description="Failed deliveries",
    )
    metadata: dict[str, Any] | None = Field(
        default=None,
        description="Additional metadata",
    )


class SubscriptionWithSecretResponse(SubscriptionResponse):
    """Subscription response including signing secret (only on creation)."""

    signing_secret: str = Field(
        ...,
        description="Webhook signing secret (only shown on creation)",
        examples=["whsec_abc123..."],
    )


class SubscriptionListResponse(BaseSchema):
    """Response schema for listing subscriptions."""

    data: list[SubscriptionResponse] = Field(
        ...,
        description="List of subscriptions",
    )
    pagination: PaginationMeta = Field(
        ...,
        description="Pagination metadata",
    )


class RotateSecretResponse(BaseSchema):
    """Response schema for rotating signing secret."""

    id: str = Field(
        ...,
        description="Subscription ID",
    )
    signing_secret: str = Field(
        ...,
        description="New signing secret",
    )
    previous_secret_valid_until: datetime = Field(
        ...,
        description="When the previous secret expires (grace period)",
    )


class TestWebhookRequest(BaseSchema):
    """Request schema for testing a webhook."""

    event_type: str = Field(
        default="test.webhook",
        description="Event type for test payload",
    )
    data: dict[str, Any] | None = Field(
        default=None,
        description="Custom test payload data",
    )


class TestWebhookResponse(BaseSchema):
    """Response schema for webhook test."""

    success: bool = Field(
        ...,
        description="Whether the test was successful",
    )
    status_code: int | None = Field(
        default=None,
        description="HTTP status code from webhook endpoint",
    )
    response_time_ms: int | None = Field(
        default=None,
        description="Response time in milliseconds",
    )
    response_body: str | None = Field(
        default=None,
        description="Response body (truncated)",
    )
    error: str | None = Field(
        default=None,
        description="Error message if test failed",
    )


class SubscriptionStatsResponse(BaseSchema):
    """Response schema for subscription statistics."""

    total_subscriptions: int = Field(
        ...,
        description="Total number of subscriptions",
    )
    active: int = Field(
        ...,
        description="Active subscriptions",
    )
    paused: int = Field(
        ...,
        description="Paused subscriptions",
    )
    disabled: int = Field(
        ...,
        description="Disabled subscriptions",
    )
    healthy: int = Field(
        ...,
        description="Healthy subscriptions",
    )
    unhealthy: int = Field(
        ...,
        description="Unhealthy subscriptions",
    )
