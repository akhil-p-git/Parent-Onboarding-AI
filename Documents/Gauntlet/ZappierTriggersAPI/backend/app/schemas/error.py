"""
Error Schemas.

RFC 7807 Problem Details format for API errors.
"""

from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FieldError(BaseModel):
    """Field-level validation error."""

    model_config = ConfigDict(populate_by_name=True)

    field: str = Field(
        ...,
        description="Field name that caused the error",
        examples=["event_type"],
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
        examples=["Field is required"],
    )
    code: str = Field(
        ...,
        description="Machine-readable error code",
        examples=["required", "invalid_format", "too_long"],
    )
    value: Any | None = Field(
        default=None,
        description="The invalid value (if safe to include)",
        examples=[""],
    )


class ProblemDetail(BaseModel):
    """
    RFC 7807 Problem Details for HTTP APIs.

    See: https://datatracker.ietf.org/doc/html/rfc7807
    """

    model_config = ConfigDict(populate_by_name=True)

    type: str = Field(
        default="about:blank",
        description="URI reference identifying the problem type",
        examples=["https://api.example.com/errors/validation"],
    )
    title: str = Field(
        ...,
        description="Short, human-readable summary of the problem",
        examples=["Validation Error"],
    )
    status: int = Field(
        ...,
        description="HTTP status code",
        examples=[400, 401, 403, 404, 422, 429, 500],
    )
    detail: str | None = Field(
        default=None,
        description="Human-readable explanation specific to this occurrence",
        examples=["The request body contains invalid fields"],
    )
    instance: str | None = Field(
        default=None,
        description="URI reference identifying the specific occurrence",
        examples=["/api/v1/events/evt_01ARZ3NDEKTSV4RRFFQ69G5FAV"],
    )

    # Extension fields
    errors: list[FieldError] | None = Field(
        default=None,
        description="Field-level validation errors",
    )
    request_id: str | None = Field(
        default=None,
        description="Unique request identifier for support",
        examples=["req_abc123xyz"],
    )
    timestamp: str | None = Field(
        default=None,
        description="When the error occurred",
        examples=["2024-01-15T10:30:00Z"],
    )


class ValidationErrorResponse(ProblemDetail):
    """Validation error response (HTTP 400/422)."""

    type: str = Field(
        default="https://api.zapier.com/errors/validation",
        description="Error type URI",
    )
    title: str = Field(
        default="Validation Error",
        description="Error title",
    )
    status: int = Field(
        default=422,
        description="HTTP status code",
    )


class AuthenticationErrorResponse(ProblemDetail):
    """Authentication error response (HTTP 401)."""

    type: str = Field(
        default="https://api.zapier.com/errors/authentication",
        description="Error type URI",
    )
    title: str = Field(
        default="Authentication Required",
        description="Error title",
    )
    status: int = Field(
        default=401,
        description="HTTP status code",
    )


class AuthorizationErrorResponse(ProblemDetail):
    """Authorization error response (HTTP 403)."""

    type: str = Field(
        default="https://api.zapier.com/errors/authorization",
        description="Error type URI",
    )
    title: str = Field(
        default="Forbidden",
        description="Error title",
    )
    status: int = Field(
        default=403,
        description="HTTP status code",
    )


class NotFoundErrorResponse(ProblemDetail):
    """Not found error response (HTTP 404)."""

    type: str = Field(
        default="https://api.zapier.com/errors/not-found",
        description="Error type URI",
    )
    title: str = Field(
        default="Resource Not Found",
        description="Error title",
    )
    status: int = Field(
        default=404,
        description="HTTP status code",
    )


class ConflictErrorResponse(ProblemDetail):
    """Conflict error response (HTTP 409)."""

    type: str = Field(
        default="https://api.zapier.com/errors/conflict",
        description="Error type URI",
    )
    title: str = Field(
        default="Resource Conflict",
        description="Error title",
    )
    status: int = Field(
        default=409,
        description="HTTP status code",
    )


class RateLimitErrorResponse(ProblemDetail):
    """Rate limit error response (HTTP 429)."""

    type: str = Field(
        default="https://api.zapier.com/errors/rate-limit",
        description="Error type URI",
    )
    title: str = Field(
        default="Rate Limit Exceeded",
        description="Error title",
    )
    status: int = Field(
        default=429,
        description="HTTP status code",
    )
    retry_after: int | None = Field(
        default=None,
        description="Seconds to wait before retrying",
        examples=[60],
    )


class InternalErrorResponse(ProblemDetail):
    """Internal server error response (HTTP 500)."""

    type: str = Field(
        default="https://api.zapier.com/errors/internal",
        description="Error type URI",
    )
    title: str = Field(
        default="Internal Server Error",
        description="Error title",
    )
    status: int = Field(
        default=500,
        description="HTTP status code",
    )


# Error response type union for OpenAPI documentation
ErrorResponse = (
    ValidationErrorResponse
    | AuthenticationErrorResponse
    | AuthorizationErrorResponse
    | NotFoundErrorResponse
    | ConflictErrorResponse
    | RateLimitErrorResponse
    | InternalErrorResponse
)
