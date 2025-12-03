"""
DLQ Commands.

Commands for managing the dead letter queue.
"""

import asyncio
from typing import Annotated, Optional

import typer

from triggers_cli.client import ApiError, TriggersClient
from triggers_cli.output import (
    print_dlq_table,
    print_error,
    print_json,
    print_stats,
    print_success,
    print_warning,
)

app = typer.Typer(help="Dead letter queue operations")


@app.command("list")
def list_dlq(
    event_type: Annotated[
        Optional[str],
        typer.Option("--type", "-t", help="Filter by event type"),
    ] = None,
    source: Annotated[
        Optional[str],
        typer.Option("--source", "-s", help="Filter by source"),
    ] = None,
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Maximum items to return"),
    ] = 20,
    offset: Annotated[
        int,
        typer.Option("--offset", help="Number of items to skip"),
    ] = 0,
    output_format: Annotated[
        str,
        typer.Option("--format", "-o", help="Output format: table, json"),
    ] = "table",
) -> None:
    """List events in the dead letter queue."""
    async def _list():
        client = TriggersClient()
        return await client.list_dlq(
            event_type=event_type,
            source=source,
            limit=limit,
            offset=offset,
        )

    try:
        result = asyncio.run(_list())
        items = result.get("data", [])
        if not items:
            print_warning("No items in dead letter queue")
            return
        print_dlq_table(items, format=output_format)

        # Show pagination info
        pagination = result.get("pagination", {})
        total = pagination.get("total", len(items))
        if total > len(items):
            print(f"\nShowing {len(items)} of {total} items")

    except ApiError as e:
        print_error(f"Failed to list DLQ: {e.message}")
        raise typer.Exit(1)


@app.command("stats")
def dlq_stats(
    output_format: Annotated[
        str,
        typer.Option("--format", "-o", help="Output format: table, json"),
    ] = "table",
) -> None:
    """Get DLQ statistics."""
    async def _stats():
        client = TriggersClient()
        # Use list endpoint to get stats
        result = await client.list_dlq(limit=1)
        total = result.get("pagination", {}).get("total", 0)
        return {"total_items": total}

    try:
        result = asyncio.run(_stats())
        if output_format == "json":
            print_json(result)
        else:
            print_stats(result, title="DLQ Statistics")
    except ApiError as e:
        print_error(f"Failed to get DLQ stats: {e.message}")
        raise typer.Exit(1)


@app.command("retry")
def retry_dlq_item(
    event_id: Annotated[str, typer.Argument(help="Event ID to retry")],
    output_format: Annotated[
        str,
        typer.Option("--format", "-o", help="Output format: table, json"),
    ] = "json",
) -> None:
    """Retry a dead-lettered event."""
    async def _retry():
        client = TriggersClient()
        return await client.retry_dlq_item(event_id)

    try:
        result = asyncio.run(_retry())
        print_success(f"Event {event_id} re-queued for processing")
        if output_format == "json":
            print_json(result)
    except ApiError as e:
        print_error(f"Failed to retry event: {e.message}")
        raise typer.Exit(1)


@app.command("retry-all")
def retry_all_dlq(
    event_type: Annotated[
        Optional[str],
        typer.Option("--type", "-t", help="Filter by event type"),
    ] = None,
    source: Annotated[
        Optional[str],
        typer.Option("--source", "-s", help="Filter by source"),
    ] = None,
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Maximum items to retry"),
    ] = 100,
    confirm: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation"),
    ] = False,
) -> None:
    """Retry all items in the DLQ matching filters."""
    if not confirm:
        confirm = typer.confirm("Are you sure you want to retry DLQ items?")
        if not confirm:
            raise typer.Exit(0)

    async def _retry_all():
        client = TriggersClient()

        # First, list items
        result = await client.list_dlq(
            event_type=event_type,
            source=source,
            limit=limit,
        )
        items = result.get("data", [])

        if not items:
            return {"retried": 0, "failed": 0}

        retried = 0
        failed = 0

        for item in items:
            try:
                await client.retry_dlq_item(item["event_id"])
                retried += 1
            except Exception:
                failed += 1

        return {"retried": retried, "failed": failed}

    try:
        result = asyncio.run(_retry_all())
        print_success(f"Retried {result['retried']} item(s), {result['failed']} failed")
    except ApiError as e:
        print_error(f"Failed to retry items: {e.message}")
        raise typer.Exit(1)


@app.command("dismiss")
def dismiss_dlq_item(
    event_id: Annotated[str, typer.Argument(help="Event ID to dismiss")],
    confirm: Annotated[
        bool,
        typer.Option("--yes", "-y", help="Skip confirmation"),
    ] = False,
) -> None:
    """Permanently dismiss an event from the DLQ."""
    if not confirm:
        confirm = typer.confirm(
            f"Are you sure you want to dismiss event {event_id}? This cannot be undone."
        )
        if not confirm:
            raise typer.Exit(0)

    async def _dismiss():
        client = TriggersClient()
        return await client.dismiss_dlq_item(event_id)

    try:
        asyncio.run(_dismiss())
        print_success(f"Event {event_id} dismissed from DLQ")
    except ApiError as e:
        print_error(f"Failed to dismiss event: {e.message}")
        raise typer.Exit(1)
