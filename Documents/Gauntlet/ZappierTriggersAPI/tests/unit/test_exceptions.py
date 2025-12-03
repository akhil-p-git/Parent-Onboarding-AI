"""
Tests for custom exception classes.
"""

import pytest

from app.core.exceptions import (
    AlreadyExistsError,
    APIKeyExpiredError,
    APIKeyRevokedError,
    AppException,
    AuthenticationError,
    AuthorizationError,
    ConflictError,
    DatabaseError,
    ErrorCode,
    EventProcessingError,
    ExternalServiceError,
    InvalidAPIKeyError,
    InvalidRequestBodyError,
    NotFoundError,
    QueueError,
    QuotaExceededError,
    RateLimitError,
    RedisError,
    SchemaValidationError,
    ServiceUnavailableError,
    SQSError,
    TimeoutError,
    ValidationError,
    WebhookDeliveryError,
)


class TestAppException:
    """Tests for base AppException."""

    def test_default_values(self):
        """Test exception with default values."""
        exc = AppException("Test error")

        assert exc.message == "Test error"
        assert exc.error_code == ErrorCode.INTERNAL_ERROR
        assert exc.status_code == 500
        assert exc.details == {}
        assert exc.instance is None

    def test_custom_values(self):
        """Test exception with custom values."""
        exc = AppException(
            message="Custom error",
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=400,
            details={"field": "email"},
            instance="/api/v1/users",
        )

        assert exc.message == "Custom error"
        assert exc.error_code == ErrorCode.VALIDATION_ERROR
        assert exc.status_code == 400
        assert exc.details == {"field": "email"}
        assert exc.instance == "/api/v1/users"

    def test_to_dict_basic(self):
        """Test converting exception to RFC 7807 dict."""
        exc = AppException("Test error")
        result = exc.to_dict()

        assert result["type"] == "https://api.example.com/errors/internal_error"
        assert result["title"] == "Internal Server Error"
        assert result["status"] == 500
        assert result["detail"] == "Test error"
        assert result["error_code"] == "internal_error"
        assert "instance" not in result
        assert "errors" not in result

    def test_to_dict_with_instance_and_details(self):
        """Test dict conversion with instance and details."""
        exc = AppException(
            message="Error with details",
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=400,
            details={"field": "name", "reason": "required"},
            instance="/api/v1/events",
        )
        result = exc.to_dict()

        assert result["instance"] == "/api/v1/events"
        assert result["errors"] == {"field": "name", "reason": "required"}


class TestAuthenticationExceptions:
    """Tests for authentication-related exceptions."""

    def test_authentication_error_defaults(self):
        """Test AuthenticationError with defaults."""
        exc = AuthenticationError()

        assert exc.status_code == 401
        assert exc.error_code == ErrorCode.AUTHENTICATION_REQUIRED
        assert "Authentication required" in exc.message

    def test_invalid_api_key_error(self):
        """Test InvalidAPIKeyError."""
        exc = InvalidAPIKeyError()

        assert exc.status_code == 401
        assert exc.error_code == ErrorCode.INVALID_API_KEY
        assert "invalid" in exc.message.lower()

    def test_api_key_expired_error(self):
        """Test APIKeyExpiredError."""
        exc = APIKeyExpiredError()

        assert exc.status_code == 401
        assert exc.error_code == ErrorCode.API_KEY_EXPIRED
        assert "expired" in exc.message.lower()

    def test_api_key_revoked_error(self):
        """Test APIKeyRevokedError."""
        exc = APIKeyRevokedError()

        assert exc.status_code == 401
        assert exc.error_code == ErrorCode.API_KEY_REVOKED
        assert "revoked" in exc.message.lower()


class TestAuthorizationError:
    """Tests for AuthorizationError."""

    def test_defaults(self):
        """Test AuthorizationError with defaults."""
        exc = AuthorizationError()

        assert exc.status_code == 403
        assert exc.error_code == ErrorCode.INSUFFICIENT_PERMISSIONS
        assert "permission" in exc.message.lower()

    def test_custom_message(self):
        """Test with custom message."""
        exc = AuthorizationError(message="Cannot delete this resource")

        assert exc.message == "Cannot delete this resource"


class TestValidationExceptions:
    """Tests for validation-related exceptions."""

    def test_validation_error_defaults(self):
        """Test ValidationError with defaults."""
        exc = ValidationError()

        assert exc.status_code == 400
        assert exc.error_code == ErrorCode.VALIDATION_ERROR

    def test_validation_error_with_field(self):
        """Test ValidationError with field parameter."""
        exc = ValidationError(message="Invalid email", field="email")

        assert exc.details == {"field": "email"}

    def test_invalid_request_body_error(self):
        """Test InvalidRequestBodyError."""
        exc = InvalidRequestBodyError()

        assert exc.status_code == 400
        assert exc.error_code == ErrorCode.INVALID_REQUEST_BODY

    def test_schema_validation_error(self):
        """Test SchemaValidationError."""
        exc = SchemaValidationError(
            details={"missing_fields": ["name", "type"]}
        )

        assert exc.status_code == 400
        assert exc.error_code == ErrorCode.SCHEMA_VALIDATION_FAILED
        assert exc.details == {"missing_fields": ["name", "type"]}


class TestNotFoundError:
    """Tests for NotFoundError."""

    def test_with_resource_type_only(self):
        """Test with just resource type."""
        exc = NotFoundError(resource_type="Event")

        assert exc.status_code == 404
        assert exc.error_code == ErrorCode.RESOURCE_NOT_FOUND
        assert "Event not found" in exc.message

    def test_with_resource_id(self):
        """Test with resource type and ID."""
        exc = NotFoundError(resource_type="Subscription", resource_id="sub_123")

        assert "sub_123" in exc.message
        assert exc.details["resource_type"] == "Subscription"
        assert exc.details["resource_id"] == "sub_123"

    def test_with_custom_message(self):
        """Test with custom message."""
        exc = NotFoundError(message="Custom not found message")

        assert exc.message == "Custom not found message"


class TestConflictErrors:
    """Tests for conflict-related exceptions."""

    def test_conflict_error(self):
        """Test ConflictError."""
        exc = ConflictError(resource_type="Event")

        assert exc.status_code == 409
        assert exc.error_code == ErrorCode.RESOURCE_CONFLICT
        assert exc.details == {"resource_type": "Event"}

    def test_already_exists_error(self):
        """Test AlreadyExistsError."""
        exc = AlreadyExistsError(resource_type="API Key", identifier="key_abc")

        assert exc.status_code == 409
        assert exc.error_code == ErrorCode.RESOURCE_ALREADY_EXISTS
        assert "already exists" in exc.message
        assert "key_abc" in exc.message


class TestRateLimitErrors:
    """Tests for rate limit exceptions."""

    def test_rate_limit_error_defaults(self):
        """Test RateLimitError with defaults."""
        exc = RateLimitError()

        assert exc.status_code == 429
        assert exc.error_code == ErrorCode.RATE_LIMIT_EXCEEDED

    def test_rate_limit_error_with_details(self):
        """Test RateLimitError with retry_after and limit."""
        exc = RateLimitError(
            retry_after=60,
            limit=100,
            remaining=0,
        )

        assert exc.retry_after == 60
        assert exc.details["retry_after_seconds"] == 60
        assert exc.details["limit"] == 100
        assert exc.details["remaining"] == 0

    def test_quota_exceeded_error(self):
        """Test QuotaExceededError."""
        exc = QuotaExceededError(
            quota_type="monthly_events",
            limit=10000,
            used=10001,
        )

        assert exc.status_code == 429
        assert exc.error_code == ErrorCode.QUOTA_EXCEEDED
        assert exc.details["quota_type"] == "monthly_events"


class TestProcessingErrors:
    """Tests for processing-related exceptions."""

    def test_event_processing_error(self):
        """Test EventProcessingError."""
        exc = EventProcessingError(
            message="Failed to process",
            event_id="evt_123",
        )

        assert exc.status_code == 500
        assert exc.error_code == ErrorCode.EVENT_PROCESSING_FAILED
        assert exc.details["event_id"] == "evt_123"

    def test_webhook_delivery_error(self):
        """Test WebhookDeliveryError."""
        exc = WebhookDeliveryError(
            webhook_url="https://example.com/webhook",
            status_code=503,
        )

        assert exc.status_code == 502
        assert exc.error_code == ErrorCode.WEBHOOK_DELIVERY_FAILED
        assert exc.details["webhook_url"] == "https://example.com/webhook"
        assert exc.details["response_status"] == 503

    def test_queue_error(self):
        """Test QueueError."""
        exc = QueueError(
            queue_name="events-queue",
            operation="send_message",
        )

        assert exc.status_code == 500
        assert exc.error_code == ErrorCode.QUEUE_OPERATION_FAILED
        assert exc.details["queue"] == "events-queue"
        assert exc.details["operation"] == "send_message"


class TestExternalServiceErrors:
    """Tests for external service exceptions."""

    def test_database_error(self):
        """Test DatabaseError."""
        exc = DatabaseError(operation="insert")

        assert exc.status_code == 500
        assert exc.error_code == ErrorCode.DATABASE_ERROR
        assert exc.details["operation"] == "insert"

    def test_redis_error(self):
        """Test RedisError."""
        exc = RedisError(operation="get")

        assert exc.status_code == 500
        assert exc.error_code == ErrorCode.REDIS_ERROR

    def test_sqs_error(self):
        """Test SQSError."""
        exc = SQSError(queue="test-queue", operation="receive")

        assert exc.status_code == 500
        assert exc.error_code == ErrorCode.SQS_ERROR

    def test_external_service_error(self):
        """Test ExternalServiceError."""
        exc = ExternalServiceError(service="PaymentAPI", status_code=502)

        assert exc.status_code == 502
        assert exc.error_code == ErrorCode.EXTERNAL_SERVICE_ERROR
        assert exc.details["service"] == "PaymentAPI"


class TestSystemErrors:
    """Tests for system-level exceptions."""

    def test_service_unavailable_error(self):
        """Test ServiceUnavailableError."""
        exc = ServiceUnavailableError(retry_after=30)

        assert exc.status_code == 503
        assert exc.error_code == ErrorCode.SERVICE_UNAVAILABLE
        assert exc.retry_after == 30

    def test_timeout_error(self):
        """Test TimeoutError."""
        exc = TimeoutError(
            operation="database_query",
            timeout_seconds=30.0,
        )

        assert exc.status_code == 504
        assert exc.error_code == ErrorCode.TIMEOUT_ERROR
        assert exc.details["operation"] == "database_query"
        assert exc.details["timeout_seconds"] == 30.0


class TestErrorCodeEnum:
    """Tests for ErrorCode enum."""

    def test_all_error_codes_have_values(self):
        """Ensure all error codes have string values."""
        for code in ErrorCode:
            assert isinstance(code.value, str)
            assert len(code.value) > 0

    def test_error_codes_are_unique(self):
        """Ensure all error code values are unique."""
        values = [code.value for code in ErrorCode]
        assert len(values) == len(set(values))
