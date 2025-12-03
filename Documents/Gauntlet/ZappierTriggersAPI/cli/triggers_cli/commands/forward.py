"""
Forward Command.

Forwards incoming events to a local development server.
"""

import asyncio
import json
from typing import Annotated, Optional

import httpx
import typer

from triggers_cli.client import ApiError, TriggersClient
from triggers_cli.config import get_config
from triggers_cli.output import console, print_error, print_success, print_warning

app = typer.Typer(help="Forward events to local server")


@app.callback(invoke_without_command=True)
def forward(
    target_url: Annotated[
        str,
        typer.Argument(help="Local URL to forward events to"),
    ],
    subscription_id: Annotated[
        Optional[str],
        typer.Option("--subscription", "-s", help="Filter by subscription ID"),
    ] = None,
    event_types: Annotated[
        Optional[str],
        typer.Option("--types", "-t", help="Comma-separated event types to filter"),
    ] = None,
    batch_size: Annotated[
        int,
        typer.Option("--batch", "-b", help="Number of events per poll"),
    ] = 10,
    interval: Annotated[
        float,
        typer.Option("--interval", "-i", help="Polling interval in seconds"),
    ] = 1.0,
    timeout: Annotated[
        int,
        typer.Option("--timeout", help="Request timeout for forwarding"),
    ] = 30,
    retry: Annotated[
        bool,
        typer.Option("--retry/--no-retry", help="Retry failed forwards"),
    ] = True,
    max_retries: Annotated[
        int,
        typer.Option("--max-retries", help="Maximum retry attempts"),
    ] = 3,
    verbose: Annotated[
        bool,
        typer.Option("--verbose", "-v", help="Show detailed output"),
    ] = False,
) -> None:
    """
    Forward events from the Triggers API to a local development server.

    This command polls the inbox and forwards each event to your local
    webhook endpoint, making it easy to test webhook integrations locally.

    Examples:
        triggers forward http://localhost:3000/webhooks
        triggers forward http://localhost:8080/api/events -s sub_123
        triggers forward http://localhost:3000/hooks -t user.created,order.completed
    """
    types_list = None
    if event_types:
        types_list = [t.strip() for t in event_types.split(",")]

    stats = {
        "received": 0,
        "forwarded": 0,
        "failed": 0,
    }

    async def forward_event(
        http_client: httpx.AsyncClient,
        event: dict,
        api_client: TriggersClient,
    ) -> bool:
        """Forward a single event to the target URL."""
        event_id = event.get("event_id", event.get("id", "unknown"))
        event_type = event.get("event_type", "unknown")

        # Build the webhook payload
        payload = {
            "id": event_id,
            "event_type": event_type,
            "source": event.get("source"),
            "data": event.get("data", {}),
            "metadata": event.get("metadata", {}),
            "timestamp": event.get("created_at"),
        }

        headers = {
            "Content-Type": "application/json",
            "X-Triggers-Event-ID": event_id,
            "X-Triggers-Event-Type": event_type,
        }

        attempts = 0
        max_attempts = max_retries + 1 if retry else 1

        while attempts < max_attempts:
            attempts += 1
            try:
                response = await http_client.post(
                    target_url,
                    json=payload,
                    headers=headers,
                    timeout=timeout,
                )

                if response.status_code < 400:
                    if verbose:
                        console.print(
                            f"[green]\u2713[/green] {event_id} -> {target_url} "
                            f"[dim]({response.status_code})[/dim]"
                        )
                    else:
                        console.print(
                            f"[green]\u2713[/green] [cyan]{event_id}[/cyan] "
                            f"[green]{event_type}[/green]"
                        )

                    # Acknowledge the event
                    receipt_handle = event.get("receipt_handle")
                    if receipt_handle:
                        try:
                            await api_client.acknowledge_events([receipt_handle])
                        except Exception as e:
                            if verbose:
                                print_warning(f"Failed to acknowledge: {e}")

                    return True

                else:
                    if verbose:
                        console.print(
                            f"[yellow]\u26a0[/yellow] {event_id} -> {response.status_code}"
                        )
                    if attempts < max_attempts:
                        await asyncio.sleep(1)  # Brief delay before retry
                    continue

            except httpx.TimeoutException:
                if verbose:
                    console.print(f"[yellow]\u26a0[/yellow] {event_id} -> timeout")
                if attempts < max_attempts:
                    await asyncio.sleep(1)
                continue

            except httpx.ConnectError:
                print_error(f"Cannot connect to {target_url}")
                return False

            except Exception as e:
                if verbose:
                    console.print(f"[red]\u2717[/red] {event_id} -> {e}")
                if attempts < max_attempts:
                    await asyncio.sleep(1)
                continue

        return False

    async def _forward():
        api_client = TriggersClient()

        console.print(f"[bold]Forwarding events to:[/bold] {target_url}")
        if subscription_id:
            console.print(f"[dim]Subscription:[/dim] {subscription_id}")
        if types_list:
            console.print(f"[dim]Event types:[/dim] {', '.join(types_list)}")
        console.print("[dim]Press Ctrl+C to stop[/dim]\n")

        async with httpx.AsyncClient() as http_client:
            # Test connection to target
            try:
                await http_client.get(target_url.rsplit("/", 1)[0] or target_url, timeout=5)
            except httpx.ConnectError:
                print_warning(f"Target server not responding at {target_url}")
                console.print("[dim]Will retry when events arrive...[/dim]\n")
            except Exception:
                pass  # Other errors are fine, we just want to check connectivity

            while True:
                try:
                    # Poll for events
                    result = await api_client.list_inbox(
                        subscription_id=subscription_id,
                        event_type=types_list[0] if types_list and len(types_list) == 1 else None,
                        limit=batch_size,
                        visibility_timeout=60,  # Give ourselves time to forward
                    )

                    items = result.get("data", [])

                    # Filter by event types if specified
                    if types_list:
                        items = [
                            item for item in items
                            if item.get("event_type") in types_list
                        ]

                    for item in items:
                        stats["received"] += 1

                        if await forward_event(http_client, item, api_client):
                            stats["forwarded"] += 1
                        else:
                            stats["failed"] += 1

                    await asyncio.sleep(interval)

                except KeyboardInterrupt:
                    break
                except ApiError as e:
                    if verbose:
                        print_error(f"API error: {e.message}")
                    await asyncio.sleep(interval * 2)  # Back off on errors
                except Exception as e:
                    if verbose:
                        print_error(f"Error: {e}")
                    await asyncio.sleep(interval * 2)

        # Print summary
        console.print("\n[bold]Summary:[/bold]")
        console.print(f"  Received:  {stats['received']}")
        console.print(f"  Forwarded: {stats['forwarded']}")
        console.print(f"  Failed:    {stats['failed']}")

    try:
        asyncio.run(_forward())
    except KeyboardInterrupt:
        pass
