"""
Dead Letter Queue API Endpoints.

Handles DLQ inspection, retry, and management operations.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import (
    CurrentApiKey,
    DBSession,
    require_scopes,
)
from app.models import ApiKey, ApiKeyScope
from app.schemas.base import PaginationMeta
from app.schemas.dlq import (
    BatchOperationResponse,
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
from app.schemas.error import NotFoundErrorResponse, ValidationErrorResponse
from app.services.dlq_service import DLQService, DLQError, DLQItemNotFoundError

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_dlq_service(db: DBSession) -> DLQService:
    """Get DLQ service instance."""
    return DLQService(db)


DLQServiceDep = Annotated[DLQService, Depends(get_dlq_service)]


@router.get(
    "",
    response_model=DLQListResponse,
    summary="List DLQ Items",
    description="List events in the dead letter queue with optional filtering.",
)
async def list_dlq_items(
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.EVENTS_READ))],
    service: DLQServiceDep,
    event_type: Annotated[
        str | None,
        Query(description="Filter by event type"),
    ] = None,
    source: Annotated[
        str | None,
        Query(description="Filter by source"),
    ] = None,
    limit: Annotated[
        int,
        Query(ge=1, le=1000, description="Max items to return"),
    ] = 100,
    offset: Annotated[
        int,
        Query(ge=0, description="Number of items to skip"),
    ] = 0,
) -> DLQListResponse:
    """
    List events in the dead letter queue.

    Returns paginated results with optional filtering by event type or source.
    Items in the DLQ represent failed events that exceeded retry limits.
    """
    items, total = await service.list_items(
        limit=limit,
        offset=offset,
        event_type=event_type,
        source=source,
    )

    return DLQListResponse(
        data=[
            DLQItemResponse(
                dlq_id=item.dlq_id,
                event_id=item.event_id,
                event_type=item.event_type,
                source=item.source,
                created_at=item.created_at,
                enqueued_at=item.enqueued_at,
                dlq_entered_at=item.dlq_entered_at,
                failure_reason=item.failure_reason,
                retry_count=item.retry_count,
            )
            for item in items
        ],
        pagination=PaginationMeta(
            limit=limit,
            has_more=(offset + len(items)) < total,
            next_cursor=None,  # Using offset pagination
            total=total,
        ),
    )


@router.get(
    "/stats",
    response_model=DLQStatsResponse,
    summary="Get DLQ Statistics",
    description="Get statistics about the dead letter queue.",
)
async def get_dlq_stats(
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.EVENTS_READ))],
    service: DLQServiceDep,
) -> DLQStatsResponse:
    """
    Get DLQ statistics.

    Returns aggregate statistics including total count and breakdown by
    event type and source.
    """
    stats = await service.get_stats()

    return DLQStatsResponse(
        total=stats["total"],
        by_event_type=stats.get("by_event_type", {}),
        by_source=stats.get("by_source", {}),
        oldest_item=stats.get("oldest_item"),
        newest_item=stats.get("newest_item"),
    )


@router.get(
    "/{event_id}",
    response_model=DLQItemResponse,
    responses={
        200: {"description": "DLQ item found"},
        404: {"model": NotFoundErrorResponse, "description": "Item not found"},
    },
    summary="Get DLQ Item",
    description="Get details of a specific DLQ item by event ID.",
)
async def get_dlq_item(
    event_id: str,
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.EVENTS_READ))],
    service: DLQServiceDep,
) -> DLQItemResponse:
    """
    Get a specific DLQ item by event ID.

    Returns full details of the dead-lettered event including
    failure information and retry count.
    """
    item = await service.get_item(event_id)

    if not item:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.zapier.com/errors/not-found",
                "title": "DLQ Item Not Found",
                "status": 404,
                "detail": f"No DLQ item found for event '{event_id}'",
                "instance": f"/api/v1/dlq/{event_id}",
            },
        )

    return DLQItemResponse(
        dlq_id=item.dlq_id,
        event_id=item.event_id,
        event_type=item.event_type,
        source=item.source,
        created_at=item.created_at,
        enqueued_at=item.enqueued_at,
        dlq_entered_at=item.dlq_entered_at,
        failure_reason=item.failure_reason,
        retry_count=item.retry_count,
    )


@router.post(
    "/{event_id}/retry",
    response_model=RetryDLQItemResponse,
    responses={
        200: {"description": "Item retried successfully"},
        404: {"model": NotFoundErrorResponse, "description": "Item not found"},
    },
    summary="Retry DLQ Item",
    description="Re-queue a dead-lettered event for delivery retry.",
)
async def retry_dlq_item(
    event_id: str,
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.EVENTS_WRITE))],
    service: DLQServiceDep,
    request: RetryDLQItemRequest | None = None,
) -> RetryDLQItemResponse:
    """
    Retry a dead-lettered event.

    Moves the event from the DLQ back to the main processing queue.
    The retry count is incremented automatically.

    Optionally, you can modify the payload before retry.
    """
    try:
        modify_payload = request.modify_payload if request else None
        result = await service.retry_item(event_id, modify_payload)

        return RetryDLQItemResponse(
            success=result["success"],
            event_id=result["event_id"],
            message=result["message"],
            retry_count=result.get("retry_count", 0),
        )

    except DLQItemNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.zapier.com/errors/not-found",
                "title": "DLQ Item Not Found",
                "status": 404,
                "detail": e.message,
            },
        )

    except DLQError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "type": "https://api.zapier.com/errors/internal",
                "title": "DLQ Operation Failed",
                "status": 500,
                "detail": e.message,
            },
        )


@router.post(
    "/retry/batch",
    response_model=BatchOperationResponse,
    summary="Retry Multiple DLQ Items",
    description="Re-queue multiple dead-lettered events at once.",
)
async def retry_dlq_batch(
    request: RetryBatchRequest,
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.EVENTS_WRITE))],
    service: DLQServiceDep,
) -> BatchOperationResponse:
    """
    Retry multiple dead-lettered events.

    Processes each event independently. Check the results array
    for individual success/failure status.
    """
    result = await service.retry_batch(request.event_ids)

    return BatchOperationResponse(
        total=result["total"],
        successful=result["successful"],
        failed=result["failed"],
        results=result["results"],
    )


@router.delete(
    "/{event_id}",
    response_model=DismissDLQItemResponse,
    responses={
        200: {"description": "Item dismissed successfully"},
        404: {"model": NotFoundErrorResponse, "description": "Item not found"},
    },
    summary="Dismiss DLQ Item",
    description="Permanently dismiss an event from the DLQ.",
)
async def dismiss_dlq_item(
    event_id: str,
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.EVENTS_WRITE))],
    service: DLQServiceDep,
) -> DismissDLQItemResponse:
    """
    Permanently dismiss a dead-lettered event.

    This removes the event from the DLQ without retrying.
    The event will be marked as permanently failed.

    Use this for events that should not be retried.
    """
    try:
        result = await service.dismiss_item(event_id)

        return DismissDLQItemResponse(
            success=result["success"],
            event_id=result["event_id"],
            message=result["message"],
        )

    except DLQItemNotFoundError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.zapier.com/errors/not-found",
                "title": "DLQ Item Not Found",
                "status": 404,
                "detail": e.message,
            },
        )

    except DLQError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "type": "https://api.zapier.com/errors/internal",
                "title": "DLQ Operation Failed",
                "status": 500,
                "detail": e.message,
            },
        )


@router.post(
    "/dismiss/batch",
    response_model=BatchOperationResponse,
    summary="Dismiss Multiple DLQ Items",
    description="Permanently dismiss multiple events from the DLQ.",
)
async def dismiss_dlq_batch(
    request: DismissBatchRequest,
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.EVENTS_WRITE))],
    service: DLQServiceDep,
) -> BatchOperationResponse:
    """
    Dismiss multiple dead-lettered events.

    Processes each event independently. Check the results array
    for individual success/failure status.
    """
    result = await service.dismiss_batch(request.event_ids)

    return BatchOperationResponse(
        total=result["total"],
        successful=result["successful"],
        failed=result["failed"],
        results=result["results"],
    )


@router.delete(
    "",
    response_model=PurgeDLQResponse,
    summary="Purge DLQ",
    description="Remove all items from the dead letter queue.",
)
async def purge_dlq(
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.EVENTS_WRITE))],
    service: DLQServiceDep,
    confirm: Annotated[
        bool,
        Query(description="Confirm purge operation"),
    ] = False,
) -> PurgeDLQResponse:
    """
    Purge all items from the DLQ.

    WARNING: This permanently removes all items. This action cannot be undone.

    You must pass confirm=true to execute this operation.
    """
    if not confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "type": "https://api.zapier.com/errors/bad-request",
                "title": "Confirmation Required",
                "status": 400,
                "detail": "Pass confirm=true to purge all DLQ items",
            },
        )

    try:
        result = await service.purge()

        return PurgeDLQResponse(
            success=result["success"],
            purged_count=result["purged_count"],
            message=result["message"],
        )

    except DLQError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "type": "https://api.zapier.com/errors/internal",
                "title": "DLQ Operation Failed",
                "status": 500,
                "detail": e.message,
            },
        )
