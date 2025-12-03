"""
Subscriptions API Endpoints.

Handles webhook subscription management for the Triggers API.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import DBSession, require_scopes
from app.models import ApiKey, ApiKeyScope, SubscriptionStatus
from app.schemas import (
    CreateSubscriptionRequest,
    PaginationMeta,
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
from app.schemas.error import NotFoundErrorResponse, ValidationErrorResponse
from app.services.subscription_service import SubscriptionService

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_subscription_service(db: DBSession) -> SubscriptionService:
    """Get subscription service instance."""
    return SubscriptionService(db)


SubscriptionServiceDep = Annotated[SubscriptionService, Depends(get_subscription_service)]


def _build_subscription_response(subscription) -> SubscriptionResponse:
    """Build subscription response from model."""
    return SubscriptionResponse(
        id=subscription.id,
        name=subscription.name,
        description=subscription.description,
        target_url=subscription.target_url,
        status=subscription.status,
        event_types=subscription.event_types,
        event_sources=subscription.event_sources,
        custom_headers=_mask_headers(subscription.custom_headers),
        webhook_config=WebhookConfig(
            timeout_seconds=subscription.timeout_seconds,
            retry_strategy=subscription.retry_strategy,
            max_retries=subscription.max_retries,
            retry_delay_seconds=subscription.retry_delay_seconds,
            retry_max_delay_seconds=subscription.retry_max_delay_seconds,
        ),
        is_healthy=subscription.is_healthy,
        consecutive_failures=subscription.consecutive_failures,
        last_success_at=subscription.last_success_at,
        last_failure_at=subscription.last_failure_at,
        last_failure_reason=subscription.last_failure_reason,
        total_deliveries=subscription.total_deliveries,
        successful_deliveries=subscription.successful_deliveries,
        failed_deliveries=subscription.failed_deliveries,
        metadata=subscription.sub_meta,
        created_at=subscription.created_at,
        updated_at=subscription.updated_at,
    )


def _mask_headers(headers: dict[str, str] | None) -> dict[str, str] | None:
    """Mask sensitive header values."""
    if not headers:
        return headers

    masked = {}
    sensitive_keys = {"authorization", "x-api-key", "api-key", "token", "secret"}

    for key, value in headers.items():
        if key.lower() in sensitive_keys:
            masked[key] = "***masked***"
        else:
            masked[key] = value

    return masked


@router.post(
    "",
    status_code=status.HTTP_201_CREATED,
    response_model=SubscriptionWithSecretResponse,
    responses={
        201: {"description": "Subscription created successfully"},
        400: {"model": ValidationErrorResponse, "description": "Validation error"},
    },
    summary="Create Subscription",
    description="Create a new webhook subscription for receiving events.",
)
async def create_subscription(
    request: CreateSubscriptionRequest,
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.SUBSCRIPTIONS_WRITE))],
    service: SubscriptionServiceDep,
) -> SubscriptionWithSecretResponse:
    """
    Create a new webhook subscription.

    The signing_secret is only returned on creation.
    Store it securely - it cannot be retrieved later.
    """
    subscription = await service.create_subscription(request, api_key_id=api_key.id)

    response = _build_subscription_response(subscription)

    return SubscriptionWithSecretResponse(
        **response.model_dump(),
        signing_secret=subscription.signing_secret,
    )


@router.get(
    "",
    response_model=SubscriptionListResponse,
    summary="List Subscriptions",
    description="Retrieve all webhook subscriptions with optional filtering.",
)
async def list_subscriptions(
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.SUBSCRIPTIONS_READ))],
    service: SubscriptionServiceDep,
    subscription_status: Annotated[
        SubscriptionStatus | None,
        Query(alias="status", description="Filter by status"),
    ] = None,
    is_healthy: Annotated[
        bool | None,
        Query(description="Filter by health status"),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=1000, description="Maximum subscriptions to return"),
    ] = 100,
    cursor: Annotated[
        str | None,
        Query(description="Pagination cursor"),
    ] = None,
) -> SubscriptionListResponse:
    """
    List all webhook subscriptions.

    Results are ordered by creation time (newest first).
    """
    subscriptions, next_cursor = await service.list_subscriptions(
        status=subscription_status,
        is_healthy=is_healthy,
        limit=limit,
        cursor=cursor,
    )

    return SubscriptionListResponse(
        data=[_build_subscription_response(s) for s in subscriptions],
        pagination=PaginationMeta(
            limit=limit,
            has_more=next_cursor is not None,
            next_cursor=next_cursor,
        ),
    )


@router.get(
    "/stats",
    response_model=SubscriptionStatsResponse,
    summary="Get Subscription Statistics",
    description="Get aggregate statistics about subscriptions.",
)
async def get_subscription_stats(
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.SUBSCRIPTIONS_READ))],
    service: SubscriptionServiceDep,
) -> SubscriptionStatsResponse:
    """Get subscription statistics."""
    stats = await service.get_stats()

    return SubscriptionStatsResponse(
        total_subscriptions=stats["total_subscriptions"],
        active=stats["active"],
        paused=stats["paused"],
        disabled=stats["disabled"],
        healthy=stats["healthy"],
        unhealthy=stats["unhealthy"],
    )


@router.get(
    "/{subscription_id}",
    response_model=SubscriptionResponse,
    responses={
        200: {"description": "Subscription found"},
        404: {"model": NotFoundErrorResponse, "description": "Subscription not found"},
    },
    summary="Get Subscription",
    description="Retrieve a specific subscription by ID.",
)
async def get_subscription(
    subscription_id: str,
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.SUBSCRIPTIONS_READ))],
    service: SubscriptionServiceDep,
) -> SubscriptionResponse:
    """
    Get subscription details by ID.

    Returns the full subscription configuration (signing secret is not included).
    """
    subscription = await service.get_subscription(subscription_id)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.zapier.com/errors/not-found",
                "title": "Subscription Not Found",
                "status": 404,
                "detail": f"Subscription with ID '{subscription_id}' not found",
                "instance": f"/api/v1/subscriptions/{subscription_id}",
            },
        )

    return _build_subscription_response(subscription)


@router.patch(
    "/{subscription_id}",
    response_model=SubscriptionResponse,
    responses={
        200: {"description": "Subscription updated"},
        404: {"model": NotFoundErrorResponse, "description": "Subscription not found"},
    },
    summary="Update Subscription",
    description="Update an existing subscription (partial update).",
)
async def update_subscription(
    subscription_id: str,
    request: UpdateSubscriptionRequest,
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.SUBSCRIPTIONS_WRITE))],
    service: SubscriptionServiceDep,
) -> SubscriptionResponse:
    """
    Update a subscription.

    Supports partial updates - only provided fields are updated.
    """
    subscription = await service.update_subscription(subscription_id, request)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.zapier.com/errors/not-found",
                "title": "Subscription Not Found",
                "status": 404,
                "detail": f"Subscription with ID '{subscription_id}' not found",
            },
        )

    return _build_subscription_response(subscription)


@router.delete(
    "/{subscription_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Subscription deleted"},
        404: {"model": NotFoundErrorResponse, "description": "Subscription not found"},
    },
    summary="Delete Subscription",
    description="Delete a webhook subscription (soft delete).",
)
async def delete_subscription(
    subscription_id: str,
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.SUBSCRIPTIONS_DELETE))],
    service: SubscriptionServiceDep,
) -> None:
    """
    Delete a subscription.

    This is a soft delete - the subscription is marked as deleted
    but retained for audit purposes.
    """
    success = await service.delete_subscription(subscription_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.zapier.com/errors/not-found",
                "title": "Subscription Not Found",
                "status": 404,
                "detail": f"Subscription with ID '{subscription_id}' not found",
            },
        )


@router.post(
    "/{subscription_id}/rotate-secret",
    response_model=RotateSecretResponse,
    responses={
        200: {"description": "Secret rotated successfully"},
        404: {"model": NotFoundErrorResponse, "description": "Subscription not found"},
    },
    summary="Rotate Signing Secret",
    description="Generate a new signing secret for the subscription.",
)
async def rotate_signing_secret(
    subscription_id: str,
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.SUBSCRIPTIONS_WRITE))],
    service: SubscriptionServiceDep,
    grace_period_hours: Annotated[
        int,
        Query(ge=1, le=168, description="Hours the old secret remains valid"),
    ] = 24,
) -> RotateSecretResponse:
    """
    Rotate the signing secret.

    The old secret remains valid for the grace period to allow
    for rolling deployments.
    """
    result = await service.rotate_signing_secret(subscription_id, grace_period_hours)

    if not result:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.zapier.com/errors/not-found",
                "title": "Subscription Not Found",
                "status": 404,
                "detail": f"Subscription with ID '{subscription_id}' not found",
            },
        )

    new_secret, old_secret_expiry = result

    return RotateSecretResponse(
        id=subscription_id,
        signing_secret=new_secret,
        previous_secret_valid_until=old_secret_expiry,
    )


@router.post(
    "/{subscription_id}/pause",
    response_model=SubscriptionResponse,
    summary="Pause Subscription",
    description="Pause event deliveries to this subscription.",
)
async def pause_subscription(
    subscription_id: str,
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.SUBSCRIPTIONS_WRITE))],
    service: SubscriptionServiceDep,
) -> SubscriptionResponse:
    """
    Pause a subscription.

    Events will be queued but not delivered until the subscription is resumed.
    """
    success = await service.pause_subscription(subscription_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.zapier.com/errors/not-found",
                "title": "Subscription Not Found",
                "status": 404,
                "detail": f"Subscription with ID '{subscription_id}' not found",
            },
        )

    subscription = await service.get_subscription(subscription_id)
    return _build_subscription_response(subscription)


@router.post(
    "/{subscription_id}/resume",
    response_model=SubscriptionResponse,
    summary="Resume Subscription",
    description="Resume event deliveries to a paused subscription.",
)
async def resume_subscription(
    subscription_id: str,
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.SUBSCRIPTIONS_WRITE))],
    service: SubscriptionServiceDep,
) -> SubscriptionResponse:
    """
    Resume a paused subscription.

    Queued events will be delivered.
    """
    success = await service.resume_subscription(subscription_id)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "type": "https://api.zapier.com/errors/bad-request",
                "title": "Cannot Resume Subscription",
                "status": 400,
                "detail": "Subscription not found or not in paused state",
            },
        )

    subscription = await service.get_subscription(subscription_id)
    return _build_subscription_response(subscription)


@router.post(
    "/{subscription_id}/test",
    response_model=TestWebhookResponse,
    summary="Test Webhook",
    description="Send a test event to the subscription's webhook URL.",
)
async def test_webhook(
    subscription_id: str,
    request: TestWebhookRequest,
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.SUBSCRIPTIONS_WRITE))],
    service: SubscriptionServiceDep,
) -> TestWebhookResponse:
    """
    Send a test webhook.

    Sends a test event to verify the webhook endpoint is working correctly.
    """
    subscription = await service.get_subscription(subscription_id)

    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.zapier.com/errors/not-found",
                "title": "Subscription Not Found",
                "status": 404,
                "detail": f"Subscription with ID '{subscription_id}' not found",
            },
        )

    # TODO: Implement actual webhook test delivery
    # For now, return a placeholder response
    import httpx
    import time

    test_payload = {
        "event_type": request.event_type,
        "source": "webhook-test",
        "data": request.data or {"test": True, "message": "This is a test webhook"},
        "timestamp": time.time(),
    }

    try:
        start = time.time()
        async with httpx.AsyncClient(timeout=subscription.timeout_seconds) as client:
            response = await client.post(
                subscription.target_url,
                json=test_payload,
                headers=subscription.custom_headers or {},
            )
        elapsed_ms = int((time.time() - start) * 1000)

        return TestWebhookResponse(
            success=200 <= response.status_code < 300,
            status_code=response.status_code,
            response_time_ms=elapsed_ms,
            response_body=response.text[:1000] if response.text else None,
            error=None if 200 <= response.status_code < 300 else f"HTTP {response.status_code}",
        )

    except httpx.TimeoutException:
        return TestWebhookResponse(
            success=False,
            status_code=None,
            response_time_ms=subscription.timeout_seconds * 1000,
            response_body=None,
            error="Request timed out",
        )

    except Exception as e:
        return TestWebhookResponse(
            success=False,
            status_code=None,
            response_time_ms=None,
            response_body=None,
            error=str(e),
        )
