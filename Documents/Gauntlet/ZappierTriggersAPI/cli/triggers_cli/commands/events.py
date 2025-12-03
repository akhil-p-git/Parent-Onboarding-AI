"""
Events Commands.

Commands for sending and managing events.
"""

import asyncio
import json
import sys
from pathlib import Path
from typing import Annotated, Optional

import typer

from triggers_cli.client import ApiError, TriggersClient
from triggers_cli.config import get_config
from triggers_cli.output import (
    console,
    print_error,
    print_event,
    print_events_table,
    print_json,
    print_streaming_event,
    print_success,
    print_warning,
)

app = typer.Typer(help="Event operations")


@app.command("send")
def send_event(
    event_type: Annotated[str, typer.Argument(help="Event type (e.g., user.created)")],
    source: Annotated[str, typer.Argument(help="Event source (e.g., my-service)")],
    data: Annotated[
        Optional[str],
        typer.Option("--data", "-d", help="Event data as JSON string"),
    ] = None,
    data_file: Annotated[
        Optional[Path],
        typer.Option("--file", "-f", help="Read event data from JSON file"),
    ] = None,
    metadata: Annotated[
        Optional[str],
        typer.Option("--metadata", "-m", help="Event metadata as JSON string"),
    ] = None,
    idempotency_key: Annotated[
        Optional[str],
        typer.Option("--idempotency-key", "-k", help="Idempotency key for deduplication"),
    ] = None,
    output_format: Annotated[
        str,
        typer.Option("--format", "-o", help="Output format: table, json"),
    ] = "table",
) -> None:
    """
    Send an event to the Triggers API.

    Examples:
        triggers events send user.created my-service -d '{"user_id": "123"}'
        triggers events send order.completed orders -f order_data.json
    """
    # Parse event data
    event_data = {}
    if data_file:
        if not data_file.exists():
            print_error(f"File not found: {data_file}")
            raise typer.Exit(1)
        try:
            event_data = json.loads(data_file.read_text())
        except json.JSONDecodeError as e:
            print_error(f"Invalid JSON in file: {e}")
            raise typer.Exit(1)
    elif data:
        try:
            event_data = json.loads(data)
        except json.JSONDecodeError as e:
            print_error(f"Invalid JSON data: {e}")
            raise typer.Exit(1)
    elif not sys.stdin.isatty():
        # Read from stdin
        try:
            event_data = json.loads(sys.stdin.read())
        except json.JSONDecodeError as e:
            print_error(f"Invalid JSON from stdin: {e}")
            raise typer.Exit(1)

    # Parse metadata
    event_metadata = None
    if metadata:
        try:
            event_metadata = json.loads(metadata)
        except json.JSONDecodeError as e:
            print_error(f"Invalid metadata JSON: {e}")
            raise typer.Exit(1)

    async def _send():
        client = TriggersClient()
        return await client.send_event(
            event_type=event_type,
            source=source,
            data=event_data,
            metadata=event_metadata,
            idempotency_key=idempotency_key,
        )

    try:
        result = asyncio.run(_send())
        print_success(f"Event created: {result.get('id')}")
        print_event(result, format=output_format)
    except ApiError as e:
        print_error(f"Failed to send event: {e.message}")
        raise typer.Exit(1)


@app.command("send-batch")
def send_events_batch(
    file: Annotated[
        Path,
        typer.Argument(help="JSON file containing array of events"),
    ],
    fail_fast: Annotated[
        bool,
        typer.Option("--fail-fast", help="Stop on first error"),
    ] = False,
    output_format: Annotated[
        str,
        typer.Option("--format", "-o", help="Output format: table, json"),
    ] = "json",
) -> None:
    """
    Send multiple events in a batch.

    The file should contain a JSON array of event objects, each with:
    - event_type (required)
    - source (required)
    - data (required)
    - metadata (optional)
    - idempotency_key (optional)
    """
    if not file.exists():
        print_error(f"File not found: {file}")
        raise typer.Exit(1)

    try:
        events = json.loads(file.read_text())
        if not isinstance(events, list):
            print_error("File must contain a JSON array of events")
            raise typer.Exit(1)
    except json.JSONDecodeError as e:
        print_error(f"Invalid JSON in file: {e}")
        raise typer.Exit(1)

    async def _send_batch():
        client = TriggersClient()
        return await client.send_events_batch(events, fail_fast=fail_fast)

    try:
        result = asyncio.run(_send_batch())
        print_success(
            f"Batch processed: {result.get('successful', 0)} successful, "
            f"{result.get('failed', 0)} failed"
        )
        if output_format == "json":
            print_json(result)
    except ApiError as e:
        print_error(f"Batch send failed: {e.message}")
        raise typer.Exit(1)


@app.command("get")
def get_event(
    event_id: Annotated[str, typer.Argument(help="Event ID to retrieve")],
    output_format: Annotated[
        str,
        typer.Option("--format", "-o", help="Output format: table, json"),
    ] = "table",
) -> None:
    """Get details of a specific event."""
    async def _get():
        client = TriggersClient()
        return await client.get_event(event_id)

    try:
        result = asyncio.run(_get())
        print_event(result, format=output_format)
    except ApiError as e:
        print_error(f"Failed to get event: {e.message}")
        raise typer.Exit(1)


@app.command("list")
def list_events(
    event_type: Annotated[
        Optional[str],
        typer.Option("--type", "-t", help="Filter by event type"),
    ] = None,
    source: Annotated[
        Optional[str],
        typer.Option("--source", "-s", help="Filter by source"),
    ] = None,
    status: Annotated[
        Optional[str],
        typer.Option("--status", help="Filter by status"),
    ] = None,
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Maximum events to return"),
    ] = 20,
    output_format: Annotated[
        str,
        typer.Option("--format", "-o", help="Output format: table, json"),
    ] = "table",
) -> None:
    """List events with optional filters."""
    async def _list():
        client = TriggersClient()
        return await client.list_events(
            event_type=event_type,
            source=source,
            status=status,
            limit=limit,
        )

    try:
        result = asyncio.run(_list())
        events = result.get("data", [])
        if not events:
            print_warning("No events found")
            return
        print_events_table(events, format=output_format)
    except ApiError as e:
        print_error(f"Failed to list events: {e.message}")
        raise typer.Exit(1)


@app.command("replay")
def replay_event(
    event_id: Annotated[str, typer.Argument(help="Event ID to replay")],
    dry_run: Annotated[
        bool,
        typer.Option("--dry-run", help="Preview without executing"),
    ] = False,
    subscription_ids: Annotated[
        Optional[str],
        typer.Option("--subscriptions", "-s", help="Comma-separated subscription IDs"),
    ] = None,
    output_format: Annotated[
        str,
        typer.Option("--format", "-o", help="Output format: table, json"),
    ] = "json",
) -> None:
    """Replay an event to subscriptions."""
    target_ids = None
    if subscription_ids:
        target_ids = [s.strip() for s in subscription_ids.split(",")]

    async def _replay():
        client = TriggersClient()
        return await client.replay_event(
            event_id=event_id,
            dry_run=dry_run,
            target_subscription_ids=target_ids,
        )

    try:
        result = asyncio.run(_replay())
        if dry_run:
            print_warning("Dry run - no event was created")
        else:
            print_success(f"Event replayed: {result.get('replay_event_id')}")
        print_json(result)
    except ApiError as e:
        print_error(f"Failed to replay event: {e.message}")
        raise typer.Exit(1)


@app.command("stream")
def stream_events(
    subscription_id: Annotated[
        Optional[str],
        typer.Option("--subscription", "-s", help="Filter by subscription ID"),
    ] = None,
    event_types: Annotated[
        Optional[str],
        typer.Option("--types", "-t", help="Comma-separated event types to filter"),
    ] = None,
) -> None:
    """
    Stream events in real-time.

    Connects to the server-sent events endpoint and displays
    events as they arrive. Press Ctrl+C to stop.
    """
    types_list = None
    if event_types:
        types_list = [t.strip() for t in event_types.split(",")]

    async def _stream():
        client = TriggersClient()
        console.print("[dim]Connecting to event stream...[/dim]")
        console.print("[dim]Press Ctrl+C to stop[/dim]\n")

        try:
            async for event in client.stream_events(
                subscription_id=subscription_id,
                event_types=types_list,
            ):
                print_streaming_event(event)
        except KeyboardInterrupt:
            console.print("\n[dim]Stream disconnected[/dim]")

    try:
        asyncio.run(_stream())
    except ApiError as e:
        print_error(f"Stream error: {e.message}")
        raise typer.Exit(1)
    except KeyboardInterrupt:
        console.print("\n[dim]Stream disconnected[/dim]")
