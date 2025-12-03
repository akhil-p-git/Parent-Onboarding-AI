"""
Inbox API Endpoints.

Handles event retrieval and acknowledgment for polling-based consumption.
"""

import logging
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from app.api.deps import DBSession, require_scopes
from app.models import ApiKey, ApiKeyScope
from app.schemas import (
    AcknowledgeRequest,
    AcknowledgeResponse,
    AcknowledgeResultItem,
    ChangeVisibilityRequest,
    ChangeVisibilityResponse,
    InboxEventItem,
    InboxListResponse,
    InboxStatsResponse,
)
from app.schemas.error import NotFoundErrorResponse, ValidationErrorResponse
from app.services.inbox_service import InboxService

logger = logging.getLogger(__name__)

router = APIRouter()


async def get_inbox_service(db: DBSession) -> InboxService:
    """Get inbox service instance."""
    return InboxService(db)


InboxServiceDep = Annotated[InboxService, Depends(get_inbox_service)]


@router.get(
    "",
    response_model=InboxListResponse,
    summary="List Inbox Events",
    description="Retrieve pending events from the inbox with visibility timeout.",
)
async def list_inbox(
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.INBOX_READ))],
    service: InboxServiceDep,
    limit: Annotated[
        int,
        Query(ge=1, le=100, description="Maximum events to return"),
    ] = 10,
    visibility_timeout: Annotated[
        int,
        Query(
            ge=1,
            le=43200,
            description="Seconds before events become visible again (max 12 hours)",
        ),
    ] = 30,
    event_type: Annotated[
        list[str] | None,
        Query(alias="type", description="Filter by event type(s)"),
    ] = None,
    source: Annotated[
        list[str] | None,
        Query(description="Filter by event source(s)"),
    ] = None,
    wait_time: Annotated[
        int,
        Query(ge=0, le=20, description="Long polling wait time in seconds"),
    ] = 0,
) -> InboxListResponse:
    """
    Fetch events from the inbox.

    Events are returned with receipt handles that must be used to acknowledge them.
    If not acknowledged within the visibility_timeout, events become visible again.

    Events are returned in oldest-first order (FIFO).
    """
    items, has_more = await service.fetch_events(
        limit=limit,
        visibility_timeout=visibility_timeout,
        event_types=event_type,
        sources=source,
        wait_time=wait_time,
    )

    events = [
        InboxEventItem(
            id=item["id"],
            event_type=item["event_type"],
            source=item["source"],
            data=item["data"],
            metadata=item["metadata"],
            created_at=item["created_at"],
            receipt_handle=item["receipt_handle"],
            visibility_timeout=item["visibility_timeout"],
            delivery_count=item["delivery_count"],
        )
        for item in items
    ]

    return InboxListResponse(
        events=events,
        count=len(events),
        has_more=has_more,
        next_poll_at=None,  # Could add rate limiting info here
    )


@router.delete(
    "/{receipt_handle}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={
        204: {"description": "Event acknowledged successfully"},
        404: {"model": NotFoundErrorResponse, "description": "Receipt handle not found or expired"},
    },
    summary="Acknowledge Event",
    description="Acknowledge a single event using its receipt handle.",
)
async def acknowledge_event(
    receipt_handle: str,
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.INBOX_READ))],
    service: InboxServiceDep,
) -> None:
    """
    Acknowledge a single event.

    Marks the event as successfully processed and removes it from the inbox.
    The receipt_handle is obtained from the list inbox response.
    """
    success = await service.acknowledge(receipt_handle)

    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.zapier.com/errors/not-found",
                "title": "Receipt Handle Not Found",
                "status": 404,
                "detail": "Receipt handle not found or has expired. The event may have already been acknowledged or the visibility timeout may have passed.",
            },
        )


@router.post(
    "/ack",
    response_model=AcknowledgeResponse,
    summary="Batch Acknowledge Events",
    description="Acknowledge multiple events at once using their receipt handles.",
)
async def batch_acknowledge(
    request: AcknowledgeRequest,
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.INBOX_READ))],
    service: InboxServiceDep,
) -> AcknowledgeResponse:
    """
    Acknowledge multiple events in a batch.

    Each receipt handle is processed independently. The response includes
    per-handle results indicating success or failure.
    """
    results = await service.acknowledge_batch(request.receipt_handles)

    successful = sum(1 for r in results if r["success"])
    failed = len(results) - successful

    return AcknowledgeResponse(
        total=len(results),
        successful=successful,
        failed=failed,
        results=[
            AcknowledgeResultItem(
                receipt_handle=r["receipt_handle"],
                success=r["success"],
                error=r["error"],
            )
            for r in results
        ],
    )


@router.post(
    "/visibility",
    response_model=ChangeVisibilityResponse,
    summary="Change Visibility Timeout",
    description="Extend or reduce the visibility timeout of an event.",
)
async def change_visibility(
    request: ChangeVisibilityRequest,
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.INBOX_READ))],
    service: InboxServiceDep,
) -> ChangeVisibilityResponse:
    """
    Change the visibility timeout of an event.

    Use this to:
    - Extend processing time (increase timeout)
    - Release an event back to the queue (set timeout to 0)

    The receipt_handle must be valid and not expired.
    """
    new_deadline = await service.change_visibility(
        receipt_handle=request.receipt_handle,
        visibility_timeout=request.visibility_timeout,
    )

    if new_deadline is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "type": "https://api.zapier.com/errors/not-found",
                "title": "Receipt Handle Not Found",
                "status": 404,
                "detail": "Receipt handle not found or has expired.",
            },
        )

    return ChangeVisibilityResponse(
        success=True,
        new_visibility_timeout=new_deadline,
    )


@router.get(
    "/stats",
    response_model=InboxStatsResponse,
    summary="Get Inbox Statistics",
    description="Get statistics about the inbox queue.",
)
async def get_inbox_stats(
    api_key: Annotated[ApiKey, Depends(require_scopes(ApiKeyScope.INBOX_READ))],
    service: InboxServiceDep,
) -> InboxStatsResponse:
    """
    Get inbox statistics.

    Returns counts of visible, in-flight, and total events,
    as well as breakdowns by event type.
    """
    stats = await service.get_stats()

    return InboxStatsResponse(
        visible=stats["visible"],
        in_flight=stats["in_flight"],
        delayed=stats["delayed"],
        total=stats["total"],
        oldest_event_at=stats["oldest_event_at"],
        by_event_type=stats["by_event_type"],
    )
