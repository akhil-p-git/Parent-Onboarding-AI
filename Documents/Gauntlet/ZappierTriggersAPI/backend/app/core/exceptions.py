"""
Custom Exception Classes.

Defines application-specific exceptions with RFC 7807 Problem Details support.
"""

from enum import Enum
from typing import Any


class ErrorCode(str, Enum):
    """Standard error codes for the API."""

    # Authentication & Authorization
    AUTHENTICATION_REQUIRED = "authentication_required"
    INVALID_API_KEY = "invalid_api_key"
    API_KEY_EXPIRED = "api_key_expired"
    API_KEY_REVOKED = "api_key_revoked"
    INSUFFICIENT_PERMISSIONS = "insufficient_permissions"

    # Validation
    VALIDATION_ERROR = "validation_error"
    INVALID_REQUEST_BODY = "invalid_request_body"
    INVALID_QUERY_PARAMETER = "invalid_query_parameter"
    INVALID_PATH_PARAMETER = "invalid_path_parameter"
    SCHEMA_VALIDATION_FAILED = "schema_validation_failed"

    # Resource Errors
    RESOURCE_NOT_FOUND = "resource_not_found"
    RESOURCE_ALREADY_EXISTS = "resource_already_exists"
    RESOURCE_CONFLICT = "resource_conflict"

    # Rate Limiting
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"
    QUOTA_EXCEEDED = "quota_exceeded"

    # Processing Errors
    EVENT_PROCESSING_FAILED = "event_processing_failed"
    WEBHOOK_DELIVERY_FAILED = "webhook_delivery_failed"
    QUEUE_OPERATION_FAILED = "queue_operation_failed"

    # External Service Errors
    DATABASE_ERROR = "database_error"
    REDIS_ERROR = "redis_error"
    SQS_ERROR = "sqs_error"
    EXTERNAL_SERVICE_ERROR = "external_service_error"

    # System Errors
    INTERNAL_ERROR = "internal_error"
    SERVICE_UNAVAILABLE = "service_unavailable"
    TIMEOUT_ERROR = "timeout_error"


class AppException(Exception):
    """
    Base application exception.

    Implements RFC 7807 Problem Details for HTTP APIs.
    https://datatracker.ietf.org/doc/html/rfc7807
    """

    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        status_code: int = 500,
        details: dict[str, Any] | None = None,
        instance: str | None = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.instance = instance

    def to_dict(self) -> dict[str, Any]:
        """Convert exception to RFC 7807 Problem Details format."""
        response = {
            "type": f"https://api.example.com/errors/{self.error_code.value}",
            "title": self._get_title(),
            "status": self.status_code,
            "detail": self.message,
            "error_code": self.error_code.value,
        }

        if self.instance:
            response["instance"] = self.instance

        if self.details:
            response["errors"] = self.details

        return response

    def _get_title(self) -> str:
        """Get human-readable title for the error."""
        titles = {
            ErrorCode.AUTHENTICATION_REQUIRED: "Authentication Required",
            ErrorCode.INVALID_API_KEY: "Invalid API Key",
            ErrorCode.API_KEY_EXPIRED: "API Key Expired",
            ErrorCode.API_KEY_REVOKED: "API Key Revoked",
            ErrorCode.INSUFFICIENT_PERMISSIONS: "Insufficient Permissions",
            ErrorCode.VALIDATION_ERROR: "Validation Error",
            ErrorCode.INVALID_REQUEST_BODY: "Invalid Request Body",
            ErrorCode.INVALID_QUERY_PARAMETER: "Invalid Query Parameter",
            ErrorCode.INVALID_PATH_PARAMETER: "Invalid Path Parameter",
            ErrorCode.SCHEMA_VALIDATION_FAILED: "Schema Validation Failed",
            ErrorCode.RESOURCE_NOT_FOUND: "Resource Not Found",
            ErrorCode.RESOURCE_ALREADY_EXISTS: "Resource Already Exists",
            ErrorCode.RESOURCE_CONFLICT: "Resource Conflict",
            ErrorCode.RATE_LIMIT_EXCEEDED: "Rate Limit Exceeded",
            ErrorCode.QUOTA_EXCEEDED: "Quota Exceeded",
            ErrorCode.EVENT_PROCESSING_FAILED: "Event Processing Failed",
            ErrorCode.WEBHOOK_DELIVERY_FAILED: "Webhook Delivery Failed",
            ErrorCode.QUEUE_OPERATION_FAILED: "Queue Operation Failed",
            ErrorCode.DATABASE_ERROR: "Database Error",
            ErrorCode.REDIS_ERROR: "Redis Error",
            ErrorCode.SQS_ERROR: "SQS Error",
            ErrorCode.EXTERNAL_SERVICE_ERROR: "External Service Error",
            ErrorCode.INTERNAL_ERROR: "Internal Server Error",
            ErrorCode.SERVICE_UNAVAILABLE: "Service Unavailable",
            ErrorCode.TIMEOUT_ERROR: "Request Timeout",
        }
        return titles.get(self.error_code, "Error")


# Authentication Exceptions
class AuthenticationError(AppException):
    """Raised when authentication fails."""

    def __init__(
        self,
        message: str = "Authentication required",
        error_code: ErrorCode = ErrorCode.AUTHENTICATION_REQUIRED,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=401,
            details=details,
        )


class InvalidAPIKeyError(AuthenticationError):
    """Raised when an API key is invalid."""

    def __init__(
        self,
        message: str = "The provided API key is invalid",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_API_KEY,
            details=details,
        )


class APIKeyExpiredError(AuthenticationError):
    """Raised when an API key has expired."""

    def __init__(
        self,
        message: str = "The API key has expired",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=ErrorCode.API_KEY_EXPIRED,
            details=details,
        )


class APIKeyRevokedError(AuthenticationError):
    """Raised when an API key has been revoked."""

    def __init__(
        self,
        message: str = "The API key has been revoked",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=ErrorCode.API_KEY_REVOKED,
            details=details,
        )


# Authorization Exceptions
class AuthorizationError(AppException):
    """Raised when authorization fails."""

    def __init__(
        self,
        message: str = "You do not have permission to perform this action",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=ErrorCode.INSUFFICIENT_PERMISSIONS,
            status_code=403,
            details=details,
        )


# Validation Exceptions
class ValidationError(AppException):
    """Raised when request validation fails."""

    def __init__(
        self,
        message: str = "Request validation failed",
        error_code: ErrorCode = ErrorCode.VALIDATION_ERROR,
        details: dict[str, Any] | None = None,
        field: str | None = None,
    ) -> None:
        if field and details is None:
            details = {"field": field}
        super().__init__(
            message=message,
            error_code=error_code,
            status_code=400,
            details=details,
        )


class InvalidRequestBodyError(ValidationError):
    """Raised when the request body is invalid."""

    def __init__(
        self,
        message: str = "The request body is invalid",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=ErrorCode.INVALID_REQUEST_BODY,
            details=details,
        )


class SchemaValidationError(ValidationError):
    """Raised when schema validation fails."""

    def __init__(
        self,
        message: str = "The event payload does not match the expected schema",
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=ErrorCode.SCHEMA_VALIDATION_FAILED,
            details=details,
        )


# Resource Exceptions
class NotFoundError(AppException):
    """Raised when a resource is not found."""

    def __init__(
        self,
        resource_type: str = "Resource",
        resource_id: str | None = None,
        message: str | None = None,
    ) -> None:
        if message is None:
            if resource_id:
                message = f"{resource_type} with ID '{resource_id}' not found"
            else:
                message = f"{resource_type} not found"

        super().__init__(
            message=message,
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            status_code=404,
            details={"resource_type": resource_type, "resource_id": resource_id}
            if resource_id
            else {"resource_type": resource_type},
        )


class ConflictError(AppException):
    """Raised when there's a resource conflict."""

    def __init__(
        self,
        message: str = "Resource conflict",
        resource_type: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        if details is None and resource_type:
            details = {"resource_type": resource_type}
        super().__init__(
            message=message,
            error_code=ErrorCode.RESOURCE_CONFLICT,
            status_code=409,
            details=details,
        )


class AlreadyExistsError(ConflictError):
    """Raised when trying to create a resource that already exists."""

    def __init__(
        self,
        resource_type: str = "Resource",
        identifier: str | None = None,
    ) -> None:
        message = f"{resource_type} already exists"
        if identifier:
            message = f"{resource_type} with identifier '{identifier}' already exists"
        super().__init__(
            message=message,
            details={"resource_type": resource_type, "identifier": identifier}
            if identifier
            else {"resource_type": resource_type},
        )
        self.error_code = ErrorCode.RESOURCE_ALREADY_EXISTS


# Rate Limiting Exceptions
class RateLimitError(AppException):
    """Raised when rate limit is exceeded."""

    def __init__(
        self,
        message: str = "Rate limit exceeded. Please retry after some time.",
        retry_after: int | None = None,
        limit: int | None = None,
        remaining: int = 0,
    ) -> None:
        details = {"remaining": remaining}
        if retry_after:
            details["retry_after_seconds"] = retry_after
        if limit:
            details["limit"] = limit

        super().__init__(
            message=message,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=429,
            details=details,
        )
        self.retry_after = retry_after


class QuotaExceededError(AppException):
    """Raised when a usage quota is exceeded."""

    def __init__(
        self,
        message: str = "Usage quota exceeded",
        quota_type: str | None = None,
        limit: int | None = None,
        used: int | None = None,
    ) -> None:
        details: dict[str, Any] = {}
        if quota_type:
            details["quota_type"] = quota_type
        if limit is not None:
            details["limit"] = limit
        if used is not None:
            details["used"] = used

        super().__init__(
            message=message,
            error_code=ErrorCode.QUOTA_EXCEEDED,
            status_code=429,
            details=details if details else None,
        )


# Processing Exceptions
class EventProcessingError(AppException):
    """Raised when event processing fails."""

    def __init__(
        self,
        message: str = "Failed to process event",
        event_id: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        if details is None:
            details = {}
        if event_id:
            details["event_id"] = event_id

        super().__init__(
            message=message,
            error_code=ErrorCode.EVENT_PROCESSING_FAILED,
            status_code=500,
            details=details if details else None,
        )


class WebhookDeliveryError(AppException):
    """Raised when webhook delivery fails."""

    def __init__(
        self,
        message: str = "Failed to deliver webhook",
        webhook_url: str | None = None,
        status_code: int | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        if details is None:
            details = {}
        if webhook_url:
            details["webhook_url"] = webhook_url
        if status_code:
            details["response_status"] = status_code

        super().__init__(
            message=message,
            error_code=ErrorCode.WEBHOOK_DELIVERY_FAILED,
            status_code=502,
            details=details if details else None,
        )


class QueueError(AppException):
    """Raised when a queue operation fails."""

    def __init__(
        self,
        message: str = "Queue operation failed",
        queue_name: str | None = None,
        operation: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        if details is None:
            details = {}
        if queue_name:
            details["queue"] = queue_name
        if operation:
            details["operation"] = operation

        super().__init__(
            message=message,
            error_code=ErrorCode.QUEUE_OPERATION_FAILED,
            status_code=500,
            details=details if details else None,
        )


# External Service Exceptions
class DatabaseError(AppException):
    """Raised when a database operation fails."""

    def __init__(
        self,
        message: str = "Database operation failed",
        operation: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        if details is None:
            details = {}
        if operation:
            details["operation"] = operation

        super().__init__(
            message=message,
            error_code=ErrorCode.DATABASE_ERROR,
            status_code=500,
            details=details if details else None,
        )


class RedisError(AppException):
    """Raised when a Redis operation fails."""

    def __init__(
        self,
        message: str = "Redis operation failed",
        operation: str | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=ErrorCode.REDIS_ERROR,
            status_code=500,
            details={"operation": operation} if operation else None,
        )


class SQSError(AppException):
    """Raised when an SQS operation fails."""

    def __init__(
        self,
        message: str = "SQS operation failed",
        queue: str | None = None,
        operation: str | None = None,
    ) -> None:
        details: dict[str, Any] = {}
        if queue:
            details["queue"] = queue
        if operation:
            details["operation"] = operation

        super().__init__(
            message=message,
            error_code=ErrorCode.SQS_ERROR,
            status_code=500,
            details=details if details else None,
        )


class ExternalServiceError(AppException):
    """Raised when an external service call fails."""

    def __init__(
        self,
        message: str = "External service call failed",
        service: str | None = None,
        status_code: int = 502,
        details: dict[str, Any] | None = None,
    ) -> None:
        if details is None:
            details = {}
        if service:
            details["service"] = service

        super().__init__(
            message=message,
            error_code=ErrorCode.EXTERNAL_SERVICE_ERROR,
            status_code=status_code,
            details=details if details else None,
        )


# System Exceptions
class ServiceUnavailableError(AppException):
    """Raised when the service is unavailable."""

    def __init__(
        self,
        message: str = "Service temporarily unavailable",
        retry_after: int | None = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code=ErrorCode.SERVICE_UNAVAILABLE,
            status_code=503,
            details={"retry_after_seconds": retry_after} if retry_after else None,
        )
        self.retry_after = retry_after


class TimeoutError(AppException):
    """Raised when an operation times out."""

    def __init__(
        self,
        message: str = "Operation timed out",
        operation: str | None = None,
        timeout_seconds: float | None = None,
    ) -> None:
        details: dict[str, Any] = {}
        if operation:
            details["operation"] = operation
        if timeout_seconds:
            details["timeout_seconds"] = timeout_seconds

        super().__init__(
            message=message,
            error_code=ErrorCode.TIMEOUT_ERROR,
            status_code=504,
            details=details if details else None,
        )
