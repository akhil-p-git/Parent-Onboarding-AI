"""
Inbox Commands.

Commands for managing the event inbox.
"""

import asyncio
from typing import Annotated, Optional

import typer

from triggers_cli.client import ApiError, TriggersClient
from triggers_cli.output import (
    print_error,
    print_inbox_table,
    print_json,
    print_stats,
    print_success,
    print_warning,
)

app = typer.Typer(help="Inbox operations")


@app.command("list")
def list_inbox(
    subscription_id: Annotated[
        Optional[str],
        typer.Option("--subscription", "-s", help="Filter by subscription ID"),
    ] = None,
    event_type: Annotated[
        Optional[str],
        typer.Option("--type", "-t", help="Filter by event type"),
    ] = None,
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Maximum items to return"),
    ] = 20,
    visibility_timeout: Annotated[
        Optional[int],
        typer.Option("--visibility", "-v", help="Visibility timeout in seconds"),
    ] = None,
    output_format: Annotated[
        str,
        typer.Option("--format", "-o", help="Output format: table, json"),
    ] = "table",
) -> None:
    """
    List pending events in the inbox.

    Events are made invisible to other consumers for the visibility
    timeout period. Use the acknowledge command to mark them as processed.
    """
    async def _list():
        client = TriggersClient()
        return await client.list_inbox(
            subscription_id=subscription_id,
            event_type=event_type,
            limit=limit,
            visibility_timeout=visibility_timeout,
        )

    try:
        result = asyncio.run(_list())
        items = result.get("data", [])
        if not items:
            print_warning("No pending events in inbox")
            return
        print_inbox_table(items, format=output_format)
    except ApiError as e:
        print_error(f"Failed to list inbox: {e.message}")
        raise typer.Exit(1)


@app.command("ack")
def acknowledge_events(
    receipt_handles: Annotated[
        str,
        typer.Argument(help="Comma-separated receipt handles to acknowledge"),
    ],
    output_format: Annotated[
        str,
        typer.Option("--format", "-o", help="Output format: table, json"),
    ] = "json",
) -> None:
    """
    Acknowledge processed events.

    After successfully processing events from the inbox, acknowledge them
    to remove them from the queue. Use the receipt handles returned by
    the list command.
    """
    handles = [h.strip() for h in receipt_handles.split(",") if h.strip()]

    if not handles:
        print_error("No receipt handles provided")
        raise typer.Exit(1)

    async def _ack():
        client = TriggersClient()
        return await client.acknowledge_events(handles)

    try:
        result = asyncio.run(_ack())
        successful = result.get("successful", 0)
        failed = result.get("failed", 0)

        if failed == 0:
            print_success(f"Acknowledged {successful} event(s)")
        else:
            print_warning(f"Acknowledged {successful}, failed {failed}")

        if output_format == "json":
            print_json(result)
    except ApiError as e:
        print_error(f"Failed to acknowledge events: {e.message}")
        raise typer.Exit(1)


@app.command("stats")
def inbox_stats(
    output_format: Annotated[
        str,
        typer.Option("--format", "-o", help="Output format: table, json"),
    ] = "table",
) -> None:
    """Get inbox statistics."""
    async def _stats():
        client = TriggersClient()
        return await client.get_inbox_stats()

    try:
        result = asyncio.run(_stats())
        if output_format == "json":
            print_json(result)
        else:
            print_stats(result, title="Inbox Statistics")
    except ApiError as e:
        print_error(f"Failed to get inbox stats: {e.message}")
        raise typer.Exit(1)


@app.command("poll")
def poll_inbox(
    subscription_id: Annotated[
        Optional[str],
        typer.Option("--subscription", "-s", help="Filter by subscription ID"),
    ] = None,
    event_type: Annotated[
        Optional[str],
        typer.Option("--type", "-t", help="Filter by event type"),
    ] = None,
    batch_size: Annotated[
        int,
        typer.Option("--batch", "-b", help="Number of events per poll"),
    ] = 10,
    visibility_timeout: Annotated[
        int,
        typer.Option("--visibility", "-v", help="Visibility timeout in seconds"),
    ] = 30,
    interval: Annotated[
        int,
        typer.Option("--interval", "-i", help="Polling interval in seconds"),
    ] = 5,
    auto_ack: Annotated[
        bool,
        typer.Option("--auto-ack", help="Automatically acknowledge events"),
    ] = False,
) -> None:
    """
    Continuously poll the inbox for events.

    Polls the inbox at regular intervals and displays incoming events.
    Press Ctrl+C to stop polling.

    With --auto-ack, events are automatically acknowledged after display.
    """
    from triggers_cli.output import console, print_streaming_event

    async def _poll():
        client = TriggersClient()
        console.print("[dim]Polling inbox...[/dim]")
        console.print("[dim]Press Ctrl+C to stop[/dim]\n")

        while True:
            try:
                result = await client.list_inbox(
                    subscription_id=subscription_id,
                    event_type=event_type,
                    limit=batch_size,
                    visibility_timeout=visibility_timeout,
                )

                items = result.get("data", [])

                for item in items:
                    print_streaming_event(item)

                    if auto_ack and item.get("receipt_handle"):
                        await client.acknowledge_events([item["receipt_handle"]])
                        console.print("[dim]  (acknowledged)[/dim]")

                await asyncio.sleep(interval)

            except KeyboardInterrupt:
                break

        console.print("\n[dim]Polling stopped[/dim]")

    try:
        asyncio.run(_poll())
    except ApiError as e:
        print_error(f"Polling error: {e.message}")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        pass
