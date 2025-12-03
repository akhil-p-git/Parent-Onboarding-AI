"""
FastAPI Dependencies.

Provides reusable dependencies for authentication, authorization, and database access.
"""

from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import parse_bearer_token
from app.models import ApiKey, ApiKeyScope
from app.services.api_key_service import ApiKeyService


class AuthenticationError(HTTPException):
    """Authentication failed exception."""

    def __init__(self, detail: str = "Invalid or missing API key"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"},
        )


class AuthorizationError(HTTPException):
    """Authorization failed exception."""

    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail,
        )


class RateLimitError(HTTPException):
    """Rate limit exceeded exception."""

    def __init__(self, retry_after: int = 60):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded",
            headers={"Retry-After": str(retry_after)},
        )


# Type aliases for cleaner dependency injection
DBSession = Annotated[AsyncSession, Depends(get_db)]


async def get_api_key_service(db: DBSession) -> ApiKeyService:
    """Get API key service instance."""
    return ApiKeyService(db)


ApiKeyServiceDep = Annotated[ApiKeyService, Depends(get_api_key_service)]


async def get_api_key(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    db: AsyncSession = Depends(get_db),
) -> ApiKey:
    """
    Extract and validate API key from request.

    Supports two authentication methods:
    1. Authorization header: `Authorization: Bearer sk_live_xxx`
    2. X-API-Key header: `X-API-Key: sk_live_xxx`

    Returns:
        ApiKey: The validated API key

    Raises:
        AuthenticationError: If authentication fails
    """
    # Try Bearer token first
    raw_key = parse_bearer_token(authorization)

    # Fall back to X-API-Key header
    if raw_key is None:
        raw_key = x_api_key

    if raw_key is None:
        raise AuthenticationError("API key required. Use Authorization header or X-API-Key header.")

    # Validate the key
    service = ApiKeyService(db)
    api_key = await service.validate_api_key(raw_key)

    if api_key is None:
        raise AuthenticationError("Invalid API key")

    # Store API key in request state for later use
    request.state.api_key = api_key

    # Record usage (fire and forget)
    await service.record_usage(api_key)

    return api_key


# Dependency type for authenticated API key
CurrentApiKey = Annotated[ApiKey, Depends(get_api_key)]


def require_scopes(*required_scopes: ApiKeyScope):
    """
    Create a dependency that requires specific scopes.

    Usage:
        @router.post("/events", dependencies=[Depends(require_scopes(ApiKeyScope.EVENTS_WRITE))])
        async def create_event(...):
            ...

    Or with direct injection:
        @router.post("/events")
        async def create_event(
            api_key: ApiKey = Depends(require_scopes(ApiKeyScope.EVENTS_WRITE))
        ):
            ...
    """

    async def scope_checker(api_key: CurrentApiKey) -> ApiKey:
        """Check that the API key has required scopes."""
        for scope in required_scopes:
            if not api_key.has_scope(scope):
                raise AuthorizationError(
                    f"This operation requires the '{scope.value}' scope"
                )
        return api_key

    return scope_checker


def require_any_scope(*required_scopes: ApiKeyScope):
    """
    Create a dependency that requires any of the specified scopes.

    Usage:
        @router.get("/events", dependencies=[Depends(require_any_scope(
            ApiKeyScope.EVENTS_READ,
            ApiKeyScope.ADMIN
        ))])
    """

    async def scope_checker(api_key: CurrentApiKey) -> ApiKey:
        """Check that the API key has at least one required scope."""
        if not api_key.has_any_scope(list(required_scopes)):
            scope_list = ", ".join(f"'{s.value}'" for s in required_scopes)
            raise AuthorizationError(
                f"This operation requires one of: {scope_list}"
            )
        return api_key

    return scope_checker


# Pre-built scope checkers for common operations
RequireEventsWrite = Depends(require_scopes(ApiKeyScope.EVENTS_WRITE))
RequireEventsRead = Depends(require_scopes(ApiKeyScope.EVENTS_READ))
RequireSubscriptionsWrite = Depends(require_scopes(ApiKeyScope.SUBSCRIPTIONS_WRITE))
RequireSubscriptionsRead = Depends(require_scopes(ApiKeyScope.SUBSCRIPTIONS_READ))
RequireSubscriptionsDelete = Depends(require_scopes(ApiKeyScope.SUBSCRIPTIONS_DELETE))
RequireInboxRead = Depends(require_scopes(ApiKeyScope.INBOX_READ))
RequireAdmin = Depends(require_scopes(ApiKeyScope.ADMIN))


async def get_optional_api_key(
    request: Request,
    authorization: Annotated[str | None, Header()] = None,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
    db: AsyncSession = Depends(get_db),
) -> ApiKey | None:
    """
    Optionally extract and validate API key.

    Same as get_api_key but returns None instead of raising error if no key provided.
    Useful for endpoints that have different behavior for authenticated vs anonymous users.
    """
    raw_key = parse_bearer_token(authorization) or x_api_key

    if raw_key is None:
        return None

    service = ApiKeyService(db)
    api_key = await service.validate_api_key(raw_key)

    if api_key is not None:
        request.state.api_key = api_key
        await service.record_usage(api_key)

    return api_key


OptionalApiKey = Annotated[ApiKey | None, Depends(get_optional_api_key)]
