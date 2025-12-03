"""
Global Exception Handlers.

FastAPI exception handlers for consistent RFC 7807 error responses.
"""

import logging
import traceback
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError as PydanticValidationError
from sqlalchemy.exc import IntegrityError, OperationalError, SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.config import settings
from app.core.exceptions import (
    AppException,
    AuthenticationError,
    DatabaseError,
    ErrorCode,
    RateLimitError,
    ServiceUnavailableError,
    ValidationError,
)

logger = logging.getLogger(__name__)


def _get_request_id(request: Request) -> str | None:
    """Extract request ID from request state or headers."""
    if hasattr(request.state, "request_id"):
        return request.state.request_id
    return request.headers.get("X-Request-ID")


def _create_error_response(
    status_code: int,
    error_code: str,
    title: str,
    detail: str,
    request: Request,
    errors: dict[str, Any] | None = None,
) -> JSONResponse:
    """Create a standardized error response in RFC 7807 format."""
    request_id = _get_request_id(request)

    content: dict[str, Any] = {
        "type": f"https://api.example.com/errors/{error_code}",
        "title": title,
        "status": status_code,
        "detail": detail,
        "error_code": error_code,
        "instance": str(request.url.path),
    }

    if request_id:
        content["request_id"] = request_id

    if errors:
        content["errors"] = errors

    return JSONResponse(status_code=status_code, content=content)


async def app_exception_handler(request: Request, exc: AppException) -> JSONResponse:
    """Handle custom application exceptions."""
    request_id = _get_request_id(request)

    # Log the exception
    log_data = {
        "error_code": exc.error_code.value,
        "status_code": exc.status_code,
        "message": exc.message,
        "path": request.url.path,
        "method": request.method,
    }
    if request_id:
        log_data["request_id"] = request_id
    if exc.details:
        log_data["details"] = exc.details

    if exc.status_code >= 500:
        logger.error(f"Application error: {exc.message}", extra=log_data)
    else:
        logger.warning(f"Client error: {exc.message}", extra=log_data)

    response = _create_error_response(
        status_code=exc.status_code,
        error_code=exc.error_code.value,
        title=exc._get_title(),
        detail=exc.message,
        request=request,
        errors=exc.details,
    )

    # Add Retry-After header for rate limit errors
    if isinstance(exc, RateLimitError) and exc.retry_after:
        response.headers["Retry-After"] = str(exc.retry_after)

    # Add Retry-After header for service unavailable
    if isinstance(exc, ServiceUnavailableError) and exc.retry_after:
        response.headers["Retry-After"] = str(exc.retry_after)

    return response


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle FastAPI/Pydantic validation errors."""
    request_id = _get_request_id(request)

    # Format validation errors
    errors: list[dict[str, Any]] = []
    for error in exc.errors():
        error_detail = {
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        if "ctx" in error:
            error_detail["context"] = error["ctx"]
        errors.append(error_detail)

    logger.warning(
        f"Validation error: {len(errors)} error(s)",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "errors": errors,
        },
    )

    return _create_error_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_code=ErrorCode.VALIDATION_ERROR.value,
        title="Validation Error",
        detail=f"Request validation failed with {len(errors)} error(s)",
        request=request,
        errors={"validation_errors": errors},
    )


async def pydantic_validation_handler(
    request: Request, exc: PydanticValidationError
) -> JSONResponse:
    """Handle Pydantic validation errors (outside of FastAPI)."""
    errors = [
        {
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"],
        }
        for error in exc.errors()
    ]

    return _create_error_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_code=ErrorCode.VALIDATION_ERROR.value,
        title="Validation Error",
        detail="Data validation failed",
        request=request,
        errors={"validation_errors": errors},
    )


async def http_exception_handler(
    request: Request, exc: StarletteHTTPException
) -> JSONResponse:
    """Handle Starlette HTTP exceptions."""
    request_id = _get_request_id(request)

    # Map status codes to error codes
    error_code_map = {
        400: ErrorCode.VALIDATION_ERROR,
        401: ErrorCode.AUTHENTICATION_REQUIRED,
        403: ErrorCode.INSUFFICIENT_PERMISSIONS,
        404: ErrorCode.RESOURCE_NOT_FOUND,
        405: ErrorCode.VALIDATION_ERROR,
        409: ErrorCode.RESOURCE_CONFLICT,
        429: ErrorCode.RATE_LIMIT_EXCEEDED,
        500: ErrorCode.INTERNAL_ERROR,
        502: ErrorCode.EXTERNAL_SERVICE_ERROR,
        503: ErrorCode.SERVICE_UNAVAILABLE,
        504: ErrorCode.TIMEOUT_ERROR,
    }

    error_code = error_code_map.get(exc.status_code, ErrorCode.INTERNAL_ERROR)

    # Map status codes to titles
    title_map = {
        400: "Bad Request",
        401: "Unauthorized",
        403: "Forbidden",
        404: "Not Found",
        405: "Method Not Allowed",
        409: "Conflict",
        429: "Too Many Requests",
        500: "Internal Server Error",
        502: "Bad Gateway",
        503: "Service Unavailable",
        504: "Gateway Timeout",
    }

    title = title_map.get(exc.status_code, "Error")

    logger.warning(
        f"HTTP error {exc.status_code}: {exc.detail}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "status_code": exc.status_code,
        },
    )

    return _create_error_response(
        status_code=exc.status_code,
        error_code=error_code.value,
        title=title,
        detail=str(exc.detail) if exc.detail else title,
        request=request,
    )


async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Handle SQLAlchemy database errors."""
    request_id = _get_request_id(request)

    # Log the full error in non-production
    if settings.is_production:
        detail = "A database error occurred"
    else:
        detail = str(exc)

    logger.error(
        f"Database error: {exc}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__,
        },
        exc_info=True,
    )

    # Handle specific SQLAlchemy errors
    if isinstance(exc, IntegrityError):
        return _create_error_response(
            status_code=status.HTTP_409_CONFLICT,
            error_code=ErrorCode.RESOURCE_CONFLICT.value,
            title="Database Conflict",
            detail="A database constraint was violated" if settings.is_production else str(exc.orig),
            request=request,
        )

    if isinstance(exc, OperationalError):
        return _create_error_response(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            error_code=ErrorCode.DATABASE_ERROR.value,
            title="Database Unavailable",
            detail="Database is temporarily unavailable",
            request=request,
        )

    return _create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code=ErrorCode.DATABASE_ERROR.value,
        title="Database Error",
        detail=detail,
        request=request,
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle all unhandled exceptions."""
    request_id = _get_request_id(request)

    # Log the full traceback
    logger.error(
        f"Unhandled exception: {exc}",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "error_type": type(exc).__name__,
            "traceback": traceback.format_exc(),
        },
        exc_info=True,
    )

    # Don't expose internal error details in production
    if settings.is_production:
        detail = "An unexpected error occurred. Please try again later."
    else:
        detail = f"{type(exc).__name__}: {str(exc)}"

    return _create_error_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_code=ErrorCode.INTERNAL_ERROR.value,
        title="Internal Server Error",
        detail=detail,
        request=request,
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers with the FastAPI app."""
    # Custom application exceptions
    app.add_exception_handler(AppException, app_exception_handler)

    # Validation exceptions
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(PydanticValidationError, pydantic_validation_handler)

    # HTTP exceptions
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)

    # Database exceptions
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)

    # Catch-all for unhandled exceptions
    app.add_exception_handler(Exception, generic_exception_handler)

    logger.info("Exception handlers registered")
