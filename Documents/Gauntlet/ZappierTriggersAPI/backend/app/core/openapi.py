"""
OpenAPI Configuration and Customization.

Defines comprehensive API documentation settings including tags,
security schemes, servers, and example responses.
"""

from typing import Any

from app.core.config import settings

# API Tags with descriptions for grouping endpoints
OPENAPI_TAGS: list[dict[str, Any]] = [
    {
        "name": "Events",
        "description": """
Event ingestion and management endpoints.

Events are the core data unit in the Triggers API. They represent actions
or state changes that can be delivered to webhooks or retrieved from the inbox.

**Key Features:**
- Single and batch event creation
- Idempotency support for safe retries
- Event filtering and pagination
- Delivery status tracking
        """,
        "externalDocs": {
            "description": "Events Guide",
            "url": "https://docs.example.com/triggers/events",
        },
    },
    {
        "name": "Inbox",
        "description": """
Polling-based event consumption (SQS-like model).

The Inbox provides a queue-based interface for consuming events. Events are
fetched with a visibility timeout and must be acknowledged after processing.

**Workflow:**
1. Fetch events with `GET /inbox` (sets visibility timeout)
2. Process the events in your application
3. Acknowledge with `DELETE /inbox/{receipt_handle}` or `POST /inbox/ack`
4. If not acknowledged, events become visible again after timeout

**Best Practices:**
- Use long polling (`wait_time`) to reduce API calls
- Set appropriate visibility timeouts for your processing time
- Implement idempotent processing for at-least-once delivery
        """,
        "externalDocs": {
            "description": "Inbox Guide",
            "url": "https://docs.example.com/triggers/inbox",
        },
    },
    {
        "name": "Subscriptions",
        "description": """
Webhook subscription management (push-based delivery).

Subscriptions define webhook endpoints that receive events automatically.
Events matching the subscription's filters are delivered in real-time.

**Features:**
- Filter by event type and source
- Configurable retry policies
- Signature verification for security
- Health monitoring and auto-disable

**Webhook Signatures:**
All webhooks include a `X-Webhook-Signature` header for verification.
Use the signing secret to validate payloads.
        """,
        "externalDocs": {
            "description": "Webhooks Guide",
            "url": "https://docs.example.com/triggers/webhooks",
        },
    },
    {
        "name": "System",
        "description": """
Health checks and system monitoring endpoints.

These endpoints do not require authentication and are designed
for load balancers, container orchestration, and monitoring systems.
        """,
    },
]


# Security Schemes
SECURITY_SCHEMES: dict[str, Any] = {
    "BearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "API Key",
        "description": """
API Key authentication using Bearer token format.

Include your API key in the Authorization header:
```
Authorization: Bearer sk_live_your_api_key_here
```

**API Key Types:**
- `sk_live_*` - Production keys with full access
- `sk_test_*` - Test keys for development
- `sk_readonly_*` - Read-only access keys

**Scopes:**
API keys can have limited scopes:
- `events:read` - Read events
- `events:write` - Create events
- `inbox:read` - Access inbox
- `subscriptions:read` - Read subscriptions
- `subscriptions:write` - Manage subscriptions
- `subscriptions:delete` - Delete subscriptions
        """,
    },
    "ApiKeyHeader": {
        "type": "apiKey",
        "in": "header",
        "name": "X-API-Key",
        "description": "Alternative: Pass API key via X-API-Key header",
    },
}


# Server configurations for different environments
def get_servers() -> list[dict[str, str]]:
    """Get server configurations based on environment."""
    if settings.is_production:
        return [
            {
                "url": "https://api.zapier-triggers.com",
                "description": "Production Server",
            },
        ]
    elif settings.APP_ENV == "staging":
        return [
            {
                "url": "https://api-staging.zapier-triggers.com",
                "description": "Staging Server",
            },
            {
                "url": "http://localhost:8000",
                "description": "Local Development",
            },
        ]
    else:
        return [
            {
                "url": "http://localhost:8000",
                "description": "Local Development",
            },
            {
                "url": "https://api-staging.zapier-triggers.com",
                "description": "Staging Server",
            },
        ]


# Example request/response payloads
EXAMPLE_EVENT = {
    "event_type": "user.created",
    "source": "auth-service",
    "data": {
        "user_id": "usr_123456",
        "email": "user@example.com",
        "name": "John Doe",
        "plan": "pro",
    },
    "metadata": {
        "correlation_id": "corr_abc123",
        "version": "1.0",
    },
    "idempotency_key": "idem_unique_key_123",
}

EXAMPLE_EVENT_RESPONSE = {
    "id": "evt_01H9QWERTY123456",
    "event_type": "user.created",
    "source": "auth-service",
    "data": {
        "user_id": "usr_123456",
        "email": "user@example.com",
        "name": "John Doe",
        "plan": "pro",
    },
    "metadata": {
        "correlation_id": "corr_abc123",
        "version": "1.0",
    },
    "status": "pending",
    "idempotency_key": "idem_unique_key_123",
    "created_at": "2024-01-15T10:30:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
    "delivery_attempts": 0,
    "successful_deliveries": 0,
    "failed_deliveries": 0,
}

EXAMPLE_SUBSCRIPTION = {
    "name": "Order Notifications",
    "description": "Webhook for order-related events",
    "target_url": "https://example.com/webhooks/orders",
    "event_types": ["order.created", "order.updated", "order.completed"],
    "event_sources": ["order-service"],
    "custom_headers": {
        "X-Custom-Header": "custom-value",
    },
    "webhook_config": {
        "timeout_seconds": 30,
        "retry_strategy": "exponential",
        "max_retries": 5,
        "retry_delay_seconds": 60,
    },
}

EXAMPLE_SUBSCRIPTION_RESPONSE = {
    "id": "sub_01H9ABCDEF123456",
    "name": "Order Notifications",
    "description": "Webhook for order-related events",
    "target_url": "https://example.com/webhooks/orders",
    "status": "active",
    "event_types": ["order.created", "order.updated", "order.completed"],
    "event_sources": ["order-service"],
    "webhook_config": {
        "timeout_seconds": 30,
        "retry_strategy": "exponential",
        "max_retries": 5,
        "retry_delay_seconds": 60,
        "retry_max_delay_seconds": 3600,
    },
    "is_healthy": True,
    "consecutive_failures": 0,
    "total_deliveries": 1250,
    "successful_deliveries": 1245,
    "failed_deliveries": 5,
    "created_at": "2024-01-10T08:00:00Z",
    "updated_at": "2024-01-15T10:30:00Z",
}

EXAMPLE_INBOX_EVENT = {
    "id": "evt_01H9QWERTY123456",
    "event_type": "order.created",
    "source": "order-service",
    "data": {
        "order_id": "ord_789",
        "total": 99.99,
        "currency": "USD",
    },
    "metadata": {},
    "created_at": "2024-01-15T10:30:00Z",
    "receipt_handle": "rh_abc123def456...",
    "visibility_timeout": "2024-01-15T10:31:00Z",
    "delivery_count": 1,
}

EXAMPLE_ERROR_RESPONSE = {
    "type": "https://api.example.com/errors/validation_error",
    "title": "Validation Error",
    "status": 422,
    "detail": "Request validation failed with 2 error(s)",
    "error_code": "validation_error",
    "instance": "/api/v1/events",
    "request_id": "req_abc123",
    "errors": {
        "validation_errors": [
            {
                "field": "body.event_type",
                "message": "Field required",
                "type": "missing",
            },
            {
                "field": "body.data",
                "message": "Field required",
                "type": "missing",
            },
        ]
    },
}


def get_openapi_description() -> str:
    """Generate the main API description."""
    return """
# Zapier Triggers API

A unified, real-time event ingestion system for the Zapier platform.

## Overview

The Triggers API provides two complementary ways to consume events:

### 1. Push Model (Webhooks)
Create subscriptions to receive events automatically via HTTP webhooks.
Best for real-time processing with low latency requirements.

### 2. Pull Model (Inbox)
Poll for events using the inbox API with visibility timeouts.
Best for batch processing or when webhook endpoints aren't available.

## Authentication

All API endpoints (except health checks) require authentication via API key:

```http
Authorization: Bearer sk_live_your_api_key_here
```

Or using the `X-API-Key` header:

```http
X-API-Key: sk_live_your_api_key_here
```

## Rate Limiting

API requests are rate limited per API key:

| Plan | Requests/minute | Burst |
|------|-----------------|-------|
| Free | 100 | 20 |
| Pro | 1,000 | 100 |
| Enterprise | 10,000 | 1,000 |

Rate limit headers are included in all responses:
- `X-RateLimit-Limit`: Maximum requests per window
- `X-RateLimit-Remaining`: Remaining requests in current window
- `X-RateLimit-Reset`: Unix timestamp when the window resets

## Idempotency

Event creation supports idempotency keys for safe retries.
Include an `idempotency_key` in your request to ensure the same
event isn't created twice:

```json
{
  "event_type": "order.created",
  "data": {"order_id": "123"},
  "idempotency_key": "order-123-created"
}
```

## Webhook Signatures

All webhook deliveries include a signature header for verification:

```
X-Webhook-Signature: sha256=abc123...
```

Verify webhooks using HMAC-SHA256:

```python
import hmac
import hashlib

def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
    expected = hmac.new(
        secret.encode(),
        payload,
        hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

## Error Handling

All errors follow the [RFC 7807](https://datatracker.ietf.org/doc/html/rfc7807)
Problem Details format:

```json
{
  "type": "https://api.example.com/errors/validation_error",
  "title": "Validation Error",
  "status": 422,
  "detail": "The event_type field is required",
  "error_code": "validation_error",
  "instance": "/api/v1/events"
}
```

## SDKs and Libraries

Official SDKs are available for:
- Python: `pip install zapier-triggers`
- Node.js: `npm install @zapier/triggers`
- Go: `go get github.com/zapier/triggers-go`

## Support

- Documentation: https://docs.example.com/triggers
- API Status: https://status.example.com
- Support: support@example.com
"""


def customize_openapi_schema(openapi_schema: dict[str, Any]) -> dict[str, Any]:
    """
    Customize the OpenAPI schema with additional metadata.

    Args:
        openapi_schema: The base OpenAPI schema from FastAPI

    Returns:
        Enhanced OpenAPI schema
    """
    # Add contact and license info
    openapi_schema["info"]["contact"] = {
        "name": "API Support",
        "url": "https://support.example.com",
        "email": "api-support@example.com",
    }

    openapi_schema["info"]["license"] = {
        "name": "Apache 2.0",
        "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    }

    openapi_schema["info"]["termsOfService"] = "https://example.com/terms"

    # Add external documentation
    openapi_schema["externalDocs"] = {
        "description": "Full API Documentation",
        "url": "https://docs.example.com/triggers",
    }

    # Add servers
    openapi_schema["servers"] = get_servers()

    # Add security schemes
    if "components" not in openapi_schema:
        openapi_schema["components"] = {}

    openapi_schema["components"]["securitySchemes"] = SECURITY_SCHEMES

    # Add global security requirement
    openapi_schema["security"] = [{"BearerAuth": []}]

    # Add x-logo for documentation tools
    openapi_schema["info"]["x-logo"] = {
        "url": "https://example.com/logo.png",
        "altText": "Zapier Triggers API",
    }

    return openapi_schema
