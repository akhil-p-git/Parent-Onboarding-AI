"""
Zapier Triggers SDK Resources.

Resource classes for interacting with specific API endpoints.
"""

from zapier_triggers.resources.events import EventsResource
from zapier_triggers.resources.inbox import InboxResource
from zapier_triggers.resources.dlq import DLQResource

__all__ = [
    "EventsResource",
    "InboxResource",
    "DLQResource",
]
