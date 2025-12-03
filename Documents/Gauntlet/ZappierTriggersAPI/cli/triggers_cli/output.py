"""
Output Formatting Utilities.

Provides consistent output formatting for CLI commands.
"""

import json
from datetime import datetime
from typing import Any

from rich.console import Console
from rich.json import JSON
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from triggers_cli.config import get_config

console = Console()
error_console = Console(stderr=True)


def print_success(message: str) -> None:
    """Print a success message."""
    console.print(f"[green]\u2713[/green] {message}")


def print_error(message: str) -> None:
    """Print an error message."""
    error_console.print(f"[red]\u2717[/red] {message}")


def print_warning(message: str) -> None:
    """Print a warning message."""
    console.print(f"[yellow]\u26a0[/yellow] {message}")


def print_info(message: str) -> None:
    """Print an info message."""
    console.print(f"[blue]\u2139[/blue] {message}")


def print_json(data: Any) -> None:
    """Print data as formatted JSON."""
    console.print(JSON(json.dumps(data, indent=2, default=str)))


def print_yaml(data: Any) -> None:
    """Print data as YAML."""
    try:
        import yaml
        console.print(yaml.dump(data, default_flow_style=False, allow_unicode=True))
    except ImportError:
        print_warning("PyYAML not installed, falling back to JSON")
        print_json(data)


def format_datetime(dt: str | datetime | None) -> str:
    """Format a datetime for display."""
    if dt is None:
        return "-"
    if isinstance(dt, str):
        try:
            dt = datetime.fromisoformat(dt.replace("Z", "+00:00"))
        except ValueError:
            return dt
    return dt.strftime("%Y-%m-%d %H:%M:%S")


def format_status(status: str) -> Text:
    """Format a status with color."""
    status_colors = {
        "pending": "yellow",
        "processing": "blue",
        "delivered": "green",
        "partially_delivered": "yellow",
        "failed": "red",
        "expired": "dim",
        "active": "green",
        "inactive": "dim",
        "healthy": "green",
        "unhealthy": "red",
        "degraded": "yellow",
    }
    color = status_colors.get(status.lower(), "white")
    return Text(status, style=color)


def print_event(event: dict[str, Any], format: str = "table") -> None:
    """Print a single event."""
    if format == "json":
        print_json(event)
        return

    table = Table(show_header=False, box=None)
    table.add_column("Field", style="dim")
    table.add_column("Value")

    table.add_row("ID", event.get("id", "-"))
    table.add_row("Type", event.get("event_type", "-"))
    table.add_row("Source", event.get("source", "-"))
    table.add_row("Status", format_status(event.get("status", "-")))
    table.add_row("Created", format_datetime(event.get("created_at")))

    if event.get("data"):
        table.add_row("Data", json.dumps(event["data"], indent=2))

    console.print(Panel(table, title="Event Details", border_style="blue"))


def print_events_table(events: list[dict[str, Any]], format: str = "table") -> None:
    """Print a table of events."""
    if format == "json":
        print_json(events)
        return

    table = Table(title="Events")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Type", style="green")
    table.add_column("Source")
    table.add_column("Status")
    table.add_column("Created")

    for event in events:
        table.add_row(
            event.get("id", "-"),
            event.get("event_type", "-"),
            event.get("source", "-"),
            format_status(event.get("status", "-")),
            format_datetime(event.get("created_at")),
        )

    console.print(table)


def print_inbox_table(items: list[dict[str, Any]], format: str = "table") -> None:
    """Print inbox items table."""
    if format == "json":
        print_json(items)
        return

    table = Table(title="Inbox")
    table.add_column("Event ID", style="cyan", no_wrap=True)
    table.add_column("Type", style="green")
    table.add_column("Source")
    table.add_column("Receipt Handle", style="dim")
    table.add_column("Received")

    for item in items:
        table.add_row(
            item.get("event_id", "-"),
            item.get("event_type", "-"),
            item.get("source", "-"),
            item.get("receipt_handle", "-")[:20] + "..." if item.get("receipt_handle") else "-",
            format_datetime(item.get("received_at")),
        )

    console.print(table)


def print_dlq_table(items: list[dict[str, Any]], format: str = "table") -> None:
    """Print DLQ items table."""
    if format == "json":
        print_json(items)
        return

    table = Table(title="Dead Letter Queue")
    table.add_column("Event ID", style="cyan", no_wrap=True)
    table.add_column("Type", style="green")
    table.add_column("Source")
    table.add_column("Retries", justify="right")
    table.add_column("Failure Reason")

    for item in items:
        table.add_row(
            item.get("event_id", "-"),
            item.get("event_type", "-"),
            item.get("source", "-"),
            str(item.get("retry_count", 0)),
            (item.get("failure_reason", "-") or "-")[:30],
        )

    console.print(table)


def print_subscriptions_table(
    subscriptions: list[dict[str, Any]],
    format: str = "table",
) -> None:
    """Print subscriptions table."""
    if format == "json":
        print_json(subscriptions)
        return

    table = Table(title="Subscriptions")
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Name", style="green")
    table.add_column("Webhook URL")
    table.add_column("Status")
    table.add_column("Event Types")

    for sub in subscriptions:
        event_types = sub.get("event_types", [])
        event_types_str = ", ".join(event_types[:3])
        if len(event_types) > 3:
            event_types_str += f" (+{len(event_types) - 3})"

        status = "active" if sub.get("is_active") else "inactive"

        table.add_row(
            sub.get("id", "-"),
            sub.get("name", "-"),
            sub.get("webhook_url", "-")[:40],
            format_status(status),
            event_types_str or "*",
        )

    console.print(table)


def print_stats(stats: dict[str, Any], title: str = "Statistics") -> None:
    """Print statistics in a panel."""
    table = Table(show_header=False, box=None)
    table.add_column("Metric", style="dim")
    table.add_column("Value", justify="right")

    for key, value in stats.items():
        if isinstance(value, dict):
            for sub_key, sub_value in value.items():
                table.add_row(f"  {sub_key}", str(sub_value))
        else:
            table.add_row(key.replace("_", " ").title(), str(value))

    console.print(Panel(table, title=title, border_style="blue"))


def print_streaming_event(event: dict[str, Any]) -> None:
    """Print a streaming event."""
    timestamp = datetime.now().strftime("%H:%M:%S")
    event_type = event.get("event_type", "unknown")
    event_id = event.get("id", event.get("event_id", "?"))

    console.print(
        f"[dim]{timestamp}[/dim] "
        f"[cyan]{event_id}[/cyan] "
        f"[green]{event_type}[/green]"
    )

    config = get_config()
    if config.verbose:
        print_json(event.get("data", {}))
