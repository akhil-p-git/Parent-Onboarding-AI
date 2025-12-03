"""
Zapier Triggers Client.

Main client class for interacting with the Triggers API.
"""

from __future__ import annotations

import logging
from types import TracebackType
from typing import Any, Self

import httpx

from zapier_triggers.exceptions import (
    AuthenticationError,
    ConflictError,
    NetworkError,
    NotFoundError,
    RateLimitError,
    ServerError,
    TriggersAPIError,
    ValidationError,
)
from zapier_triggers.resources.events import EventsResource
from zapier_triggers.resources.inbox import InboxResource
from zapier_triggers.resources.dlq import DLQResource

logger = logging.getLogger(__name__)


DEFAULT_BASE_URL = "http://localhost:8000"
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3


class TriggersClient:
    """
    Async client for the Zapier Triggers API.

    This is the main entry point for interacting with the API.
    Use it as an async context manager to ensure proper cleanup.

    Example:
        ```python
        async with TriggersClient(api_key="your_key") as client:
            event = await client.events.create(
                event_type="user.created",
                source="my-app",
                data={"user_id": "123"},
            )
        ```

    Attributes:
        events: Resource for event operations
        inbox: Resource for inbox operations
        dlq: Resource for dead letter queue operations
    """

    def __init__(
        self,
        api_key: str | None = None,
        base_url: str = DEFAULT_BASE_URL,
        timeout: float = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        """
        Initialize the Triggers client.

        Args:
            api_key: API key for authentication. Can also be set via
                     TRIGGERS_API_KEY environment variable.
            base_url: Base URL for the API. Defaults to localhost.
            timeout: Request timeout in seconds.
            max_retries: Maximum number of retries for failed requests.
            http_client: Optional pre-configured httpx client.
        """
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._owns_client = http_client is None

        if http_client is not None:
            self._client = http_client
        else:
            self._client = httpx.AsyncClient(
                base_url=self._base_url,
                timeout=timeout,
                headers=self._build_headers(),
            )

        # Initialize resources
        self.events = EventsResource(self)
        self.inbox = InboxResource(self)
        self.dlq = DLQResource(self)

    def _build_headers(self) -> dict[str, str]:
        """Build default headers for requests."""
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": "zapier-triggers-python/0.1.0",
        }
        if self._api_key:
            headers["Authorization"] = f"Bearer {self._api_key}"
        return headers

    async def __aenter__(self) -> Self:
        """Enter async context."""
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Exit async context and cleanup."""
        await self.close()

    async def close(self) -> None:
        """Close the HTTP client."""
        if self._owns_client:
            await self._client.aclose()

    async def request(
        self,
        method: str,
        path: str,
        *,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> httpx.Response:
        """
        Make an HTTP request to the API.

        This method handles authentication, error handling, and retries.

        Args:
            method: HTTP method (GET, POST, PUT, DELETE, etc.)
            path: API path (e.g., "/api/v1/events")
            params: Query parameters
            json: JSON request body
            headers: Additional headers

        Returns:
            The HTTP response

        Raises:
            AuthenticationError: If authentication fails
            ValidationError: If request validation fails
            NotFoundError: If the resource is not found
            RateLimitError: If rate limit is exceeded
            ServerError: If the server returns a 5xx error
            NetworkError: If a network error occurs
        """
        url = f"{self._base_url}{path}"

        request_headers = self._build_headers()
        if headers:
            request_headers.update(headers)

        last_error: Exception | None = None

        for attempt in range(self._max_retries):
            try:
                response = await self._client.request(
                    method=method,
                    url=url,
                    params=params,
                    json=json,
                    headers=request_headers,
                )

                # Handle errors
                if response.status_code >= 400:
                    self._handle_error_response(response)

                return response

            except httpx.TimeoutException as e:
                last_error = NetworkError(
                    f"Request timed out after {self._timeout}s",
                    details={"attempt": attempt + 1},
                )
                logger.warning(f"Request timeout (attempt {attempt + 1}): {e}")

            except httpx.NetworkError as e:
                last_error = NetworkError(
                    f"Network error: {e}",
                    details={"attempt": attempt + 1},
                )
                logger.warning(f"Network error (attempt {attempt + 1}): {e}")

            except TriggersAPIError:
                # Don't retry client errors (4xx)
                raise

            except Exception as e:
                last_error = NetworkError(
                    f"Unexpected error: {e}",
                    details={"attempt": attempt + 1},
                )
                logger.error(f"Unexpected error (attempt {attempt + 1}): {e}")

        # All retries exhausted
        if last_error:
            raise last_error
        raise NetworkError("Request failed after all retries")

    def _handle_error_response(self, response: httpx.Response) -> None:
        """Handle error responses and raise appropriate exceptions."""
        status_code = response.status_code

        try:
            error_data = response.json()
            detail = error_data.get("detail", {})
            if isinstance(detail, str):
                message = detail
                error_type = None
                details = {}
            else:
                message = detail.get("detail", detail.get("message", "Unknown error"))
                error_type = detail.get("type")
                details = detail
        except Exception:
            message = response.text or f"HTTP {status_code}"
            error_type = None
            details = {}

        if status_code == 401:
            raise AuthenticationError(
                message=message,
                status_code=status_code,
                error_type=error_type,
                details=details,
            )
        elif status_code == 403:
            raise AuthenticationError(
                message=message or "Forbidden",
                status_code=status_code,
                error_type=error_type,
                details=details,
            )
        elif status_code == 404:
            raise NotFoundError(
                message=message,
                status_code=status_code,
                error_type=error_type,
                details=details,
            )
        elif status_code == 409:
            raise ConflictError(
                message=message,
                status_code=status_code,
                error_type=error_type,
                details=details,
                existing_resource_id=details.get("existing_event_id"),
            )
        elif status_code == 422:
            raise ValidationError(
                message=message,
                status_code=status_code,
                error_type=error_type,
                details=details,
                validation_errors=details.get("errors", []),
            )
        elif status_code == 429:
            retry_after = response.headers.get("Retry-After")
            raise RateLimitError(
                message=message or "Rate limit exceeded",
                status_code=status_code,
                error_type=error_type,
                details=details,
                retry_after=int(retry_after) if retry_after else None,
            )
        elif status_code >= 500:
            raise ServerError(
                message=message or "Server error",
                status_code=status_code,
                error_type=error_type,
                details=details,
            )
        else:
            raise TriggersAPIError(
                message=message,
                status_code=status_code,
                error_type=error_type,
                details=details,
            )

    async def health(self) -> dict[str, Any]:
        """
        Check API health status.

        Returns:
            Health status information including component health.

        Example:
            ```python
            health = await client.health()
            print(f"Status: {health['status']}")
            ```
        """
        response = await self.request("GET", "/api/v1/health")
        return response.json()
