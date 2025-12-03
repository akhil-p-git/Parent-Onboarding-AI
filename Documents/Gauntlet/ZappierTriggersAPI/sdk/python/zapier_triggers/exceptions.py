"""
Zapier Triggers SDK Exceptions.

Custom exception classes for API errors.
"""

from typing import Any


class TriggersAPIError(Exception):
    """Base exception for all Triggers API errors."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        error_type: str | None = None,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Initialize the API error.

        Args:
            message: Human-readable error message
            status_code: HTTP status code from the response
            error_type: API error type identifier
            details: Additional error details from the API
        """
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.error_type = error_type
        self.details = details or {}

    def __str__(self) -> str:
        if self.status_code:
            return f"[{self.status_code}] {self.message}"
        return self.message

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"message={self.message!r}, "
            f"status_code={self.status_code!r}, "
            f"error_type={self.error_type!r})"
        )


class AuthenticationError(TriggersAPIError):
    """
    Raised when authentication fails.

    This typically occurs when:
    - API key is missing or invalid
    - API key has been revoked
    - API key doesn't have required scopes
    """

    pass


class ValidationError(TriggersAPIError):
    """
    Raised when request validation fails.

    This occurs when the request body or parameters
    don't meet the API's validation requirements.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        error_type: str | None = None,
        details: dict[str, Any] | None = None,
        validation_errors: list[dict[str, Any]] | None = None,
    ) -> None:
        """
        Initialize the validation error.

        Args:
            message: Human-readable error message
            status_code: HTTP status code
            error_type: API error type identifier
            details: Additional error details
            validation_errors: List of field-specific validation errors
        """
        super().__init__(message, status_code, error_type, details)
        self.validation_errors = validation_errors or []


class NotFoundError(TriggersAPIError):
    """
    Raised when a resource is not found.

    This occurs when trying to access an event, subscription,
    or other resource that doesn't exist.
    """

    pass


class RateLimitError(TriggersAPIError):
    """
    Raised when rate limit is exceeded.

    Check the `retry_after` attribute to know when
    you can retry the request.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        error_type: str | None = None,
        details: dict[str, Any] | None = None,
        retry_after: int | None = None,
    ) -> None:
        """
        Initialize the rate limit error.

        Args:
            message: Human-readable error message
            status_code: HTTP status code
            error_type: API error type identifier
            details: Additional error details
            retry_after: Seconds to wait before retrying
        """
        super().__init__(message, status_code, error_type, details)
        self.retry_after = retry_after


class ConflictError(TriggersAPIError):
    """
    Raised when there's a conflict, such as duplicate idempotency key.

    The `existing_resource_id` may contain the ID of the
    existing resource that caused the conflict.
    """

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        error_type: str | None = None,
        details: dict[str, Any] | None = None,
        existing_resource_id: str | None = None,
    ) -> None:
        """
        Initialize the conflict error.

        Args:
            message: Human-readable error message
            status_code: HTTP status code
            error_type: API error type identifier
            details: Additional error details
            existing_resource_id: ID of the existing conflicting resource
        """
        super().__init__(message, status_code, error_type, details)
        self.existing_resource_id = existing_resource_id


class ServerError(TriggersAPIError):
    """
    Raised when the server encounters an internal error.

    These errors are typically transient and can be retried.
    """

    pass


class NetworkError(TriggersAPIError):
    """
    Raised when a network-level error occurs.

    This includes connection timeouts, DNS failures,
    and other transport-level issues.
    """

    pass
