"""
Pydantic Schemas Package.

All request/response schemas are exported from this module.
"""

# Base schemas
from app.schemas.base import (
    BaseSchema,
    MetadataField,
    PaginatedResponse,
    PaginationMeta,
    PaginationParams,
    SuccessResponse,
    TimestampMixin,
)

# Error schemas
from app.schemas.error import (
    AuthenticationErrorResponse,
    AuthorizationErrorResponse,
    ConflictErrorResponse,
    ErrorResponse,
    FieldError,
    InternalErrorResponse,
    NotFoundErrorResponse,
    ProblemDetail,
    RateLimitErrorResponse,
    ValidationErrorResponse,
)

# Event schemas
from app.schemas.event import (
    CreateEventRequest,
    EventFilterParams,
    EventListResponse,
    EventResponse,
    EventStatsResponse,
    ReplayEventRequest,
    ReplayEventResponse,
    ReplayPreviewResponse,
)

# Batch schemas
from app.schemas.batch import (
    BatchCreateEventRequest,
    BatchCreateEventResponse,
    BatchEventError,
    BatchEventItem,
    BatchEventResultItem,
    BatchEventSummary,
)

# Inbox schemas
from app.schemas.inbox import (
    AcknowledgeRequest,
    AcknowledgeResponse,
    AcknowledgeResultItem,
    ChangeVisibilityRequest,
    ChangeVisibilityResponse,
    InboxEventItem,
    InboxListRequest,
    InboxListResponse,
    InboxStatsResponse,
)

# Subscription schemas
from app.schemas.subscription import (
    CreateSubscriptionRequest,
    EventFilter,
    RotateSecretResponse,
    SubscriptionListResponse,
    SubscriptionResponse,
    SubscriptionStatsResponse,
    SubscriptionWithSecretResponse,
    TestWebhookRequest,
    TestWebhookResponse,
    UpdateSubscriptionRequest,
    WebhookConfig,
)

# API Key schemas
from app.schemas.api_key import (
    ApiKeyListResponse,
    ApiKeyResponse,
    ApiKeyUsageStats,
    ApiKeyWithSecretResponse,
    AvailableScopesResponse,
    CreateApiKeyRequest,
    RevokeApiKeyRequest,
    RevokeApiKeyResponse,
    ScopeInfo,
    UpdateApiKeyRequest,
)

# Health schemas
from app.schemas.health import (
    ComponentHealth,
    HealthResponse,
    HealthStatus,
    LivenessResponse,
    MetricsResponse,
    ReadinessResponse,
    SystemInfoResponse,
)

# DLQ schemas
from app.schemas.dlq import (
    BatchOperationResponse,
    BatchResultItem,
    DismissBatchRequest,
    DismissDLQItemResponse,
    DLQItemResponse,
    DLQListResponse,
    DLQStatsResponse,
    PurgeDLQResponse,
    RetryBatchRequest,
    RetryDLQItemRequest,
    RetryDLQItemResponse,
)

__all__ = [
    # Base
    "BaseSchema",
    "TimestampMixin",
    "PaginationParams",
    "PaginatedResponse",
    "PaginationMeta",
    "SuccessResponse",
    "MetadataField",
    # Errors
    "FieldError",
    "ProblemDetail",
    "ValidationErrorResponse",
    "AuthenticationErrorResponse",
    "AuthorizationErrorResponse",
    "NotFoundErrorResponse",
    "ConflictErrorResponse",
    "RateLimitErrorResponse",
    "InternalErrorResponse",
    "ErrorResponse",
    # Events
    "CreateEventRequest",
    "EventResponse",
    "EventListResponse",
    "EventFilterParams",
    "EventStatsResponse",
    "ReplayEventRequest",
    "ReplayEventResponse",
    "ReplayPreviewResponse",
    # Batch
    "BatchEventItem",
    "BatchCreateEventRequest",
    "BatchEventResultItem",
    "BatchEventError",
    "BatchCreateEventResponse",
    "BatchEventSummary",
    # Inbox
    "InboxEventItem",
    "InboxListRequest",
    "InboxListResponse",
    "AcknowledgeRequest",
    "AcknowledgeResultItem",
    "AcknowledgeResponse",
    "ChangeVisibilityRequest",
    "ChangeVisibilityResponse",
    "InboxStatsResponse",
    # Subscriptions
    "WebhookConfig",
    "EventFilter",
    "CreateSubscriptionRequest",
    "UpdateSubscriptionRequest",
    "SubscriptionResponse",
    "SubscriptionWithSecretResponse",
    "SubscriptionListResponse",
    "RotateSecretResponse",
    "TestWebhookRequest",
    "TestWebhookResponse",
    "SubscriptionStatsResponse",
    # API Keys
    "CreateApiKeyRequest",
    "UpdateApiKeyRequest",
    "ApiKeyResponse",
    "ApiKeyWithSecretResponse",
    "ApiKeyListResponse",
    "RevokeApiKeyRequest",
    "RevokeApiKeyResponse",
    "ApiKeyUsageStats",
    "AvailableScopesResponse",
    "ScopeInfo",
    # Health
    "HealthStatus",
    "ComponentHealth",
    "HealthResponse",
    "ReadinessResponse",
    "LivenessResponse",
    "SystemInfoResponse",
    "MetricsResponse",
    # DLQ
    "DLQItemResponse",
    "DLQListResponse",
    "DLQStatsResponse",
    "RetryDLQItemRequest",
    "RetryDLQItemResponse",
    "RetryBatchRequest",
    "DismissDLQItemResponse",
    "DismissBatchRequest",
    "BatchOperationResponse",
    "BatchResultItem",
    "PurgeDLQResponse",
]
