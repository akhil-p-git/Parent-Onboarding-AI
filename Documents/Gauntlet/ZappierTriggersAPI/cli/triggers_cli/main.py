"""
Triggers CLI - Main Entry Point.

Command-line tool for interacting with the Zapier Triggers API.
"""

import asyncio
from typing import Annotated, Optional

import typer
from rich.console import Console

from triggers_cli import __version__
from triggers_cli.client import ApiError, TriggersClient
from triggers_cli.commands import dlq, events, forward, inbox
from triggers_cli.config import get_config, save_config, set_config
from triggers_cli.output import print_error, print_json, print_success

# Create the main app
app = typer.Typer(
    name="triggers",
    help="Command-line tool for the Zapier Triggers API",
    no_args_is_help=True,
    rich_markup_mode="rich",
)

# Add sub-commands
app.add_typer(events.app, name="events", help="Event operations")
app.add_typer(inbox.app, name="inbox", help="Inbox operations")
app.add_typer(dlq.app, name="dlq", help="Dead letter queue operations")
app.add_typer(forward.app, name="forward", help="Forward events to local server")

console = Console()


def version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print(f"triggers-cli version {__version__}")
        raise typer.Exit()


@app.callback()
def main(
    api_url: Annotated[
        Optional[str],
        typer.Option(
            "--api-url",
            "-u",
            envvar="TRIGGERS_API_URL",
            help="Triggers API base URL",
        ),
    ] = None,
    api_key: Annotated[
        Optional[str],
        typer.Option(
            "--api-key",
            "-k",
            envvar="TRIGGERS_API_KEY",
            help="API key for authentication",
        ),
    ] = None,
    output_format: Annotated[
        Optional[str],
        typer.Option(
            "--format",
            "-o",
            help="Default output format: table, json",
        ),
    ] = None,
    verbose: Annotated[
        bool,
        typer.Option(
            "--verbose",
            "-v",
            help="Enable verbose output",
        ),
    ] = False,
    version: Annotated[
        Optional[bool],
        typer.Option(
            "--version",
            "-V",
            callback=version_callback,
            is_eager=True,
            help="Show version and exit",
        ),
    ] = None,
) -> None:
    """
    Triggers CLI - Interact with the Zapier Triggers API.

    Configure authentication using environment variables or command-line options:

        export TRIGGERS_API_URL=https://api.example.com
        export TRIGGERS_API_KEY=your_api_key

    Or pass them directly:

        triggers --api-url https://api.example.com --api-key your_key events list
    """
    # Update config with CLI options
    set_config(
        api_url=api_url,
        api_key=api_key,
        output_format=output_format,
        verbose=verbose,
    )


@app.command("config")
def show_config(
    set_url: Annotated[
        Optional[str],
        typer.Option("--set-url", help="Set API URL"),
    ] = None,
    set_key: Annotated[
        Optional[str],
        typer.Option("--set-key", help="Set API key"),
    ] = None,
    show: Annotated[
        bool,
        typer.Option("--show", "-s", help="Show current configuration"),
    ] = False,
) -> None:
    """View or update CLI configuration."""
    config = get_config()

    if set_url or set_key:
        config = set_config(api_url=set_url, api_key=set_key)
        save_config(config)
        print_success("Configuration saved")

    if show or (not set_url and not set_key):
        console.print("[bold]Current Configuration:[/bold]")
        console.print(f"  API URL:  {config.api_url}")
        console.print(f"  API Key:  {'*' * 8 + config.api_key[-4:] if config.api_key else '[dim]not set[/dim]'}")
        console.print(f"  Format:   {config.output_format}")
        console.print(f"  Timeout:  {config.timeout}s")


@app.command("health")
def check_health(
    output_format: Annotated[
        str,
        typer.Option("--format", "-o", help="Output format: table, json"),
    ] = "table",
) -> None:
    """Check API health status."""
    async def _health():
        client = TriggersClient()
        return await client.health_check()

    try:
        result = asyncio.run(_health())

        if output_format == "json":
            print_json(result)
        else:
            status = result.get("status", "unknown")
            if status == "healthy":
                print_success(f"API is healthy (v{result.get('version', '?')})")
            else:
                print_error(f"API status: {status}")

            components = result.get("components", {})
            if components:
                console.print("\n[bold]Components:[/bold]")
                for name, comp_status in components.items():
                    icon = "\u2713" if comp_status == "healthy" else "\u2717"
                    color = "green" if comp_status == "healthy" else "red"
                    console.print(f"  [{color}]{icon}[/{color}] {name}: {comp_status}")

    except ApiError as e:
        print_error(f"Health check failed: {e.message}")
        raise typer.Exit(1)
    except Exception as e:
        print_error(f"Cannot connect to API: {e}")
        raise typer.Exit(1)


@app.command("subscriptions")
def list_subscriptions(
    output_format: Annotated[
        str,
        typer.Option("--format", "-o", help="Output format: table, json"),
    ] = "table",
    limit: Annotated[
        int,
        typer.Option("--limit", "-n", help="Maximum items to return"),
    ] = 20,
) -> None:
    """List subscriptions."""
    from triggers_cli.output import print_subscriptions_table, print_warning

    async def _list():
        client = TriggersClient()
        return await client.list_subscriptions(limit=limit)

    try:
        result = asyncio.run(_list())
        items = result.get("data", [])
        if not items:
            print_warning("No subscriptions found")
            return
        print_subscriptions_table(items, format=output_format)
    except ApiError as e:
        print_error(f"Failed to list subscriptions: {e.message}")
        raise typer.Exit(1)


# Shortcut commands for common operations

@app.command("send", hidden=True)
def send_shortcut(
    event_type: Annotated[str, typer.Argument(help="Event type")],
    source: Annotated[str, typer.Argument(help="Event source")],
    data: Annotated[
        Optional[str],
        typer.Option("--data", "-d", help="Event data as JSON"),
    ] = None,
) -> None:
    """Shortcut for 'events send'."""
    events.send_event(
        event_type=event_type,
        source=source,
        data=data,
        data_file=None,
        metadata=None,
        idempotency_key=None,
        output_format="table",
    )


@app.command("stream", hidden=True)
def stream_shortcut(
    subscription_id: Annotated[
        Optional[str],
        typer.Option("--subscription", "-s", help="Subscription ID"),
    ] = None,
) -> None:
    """Shortcut for 'events stream'."""
    events.stream_events(
        subscription_id=subscription_id,
        event_types=None,
    )


if __name__ == "__main__":
    app()
