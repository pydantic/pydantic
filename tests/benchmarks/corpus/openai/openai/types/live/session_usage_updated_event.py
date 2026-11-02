# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .session_usage import SessionUsage

class ContextWindow(BaseModel):
    """The latest measured Live context-window usage.

    Omitted when the context limit is unknown.
    """
    usage_ratio: float

class SessionUsageUpdatedEvent(BaseModel):
    """
    Reports cumulative Live audio usage and, when available, the most recent context-window usage. Delegated Responses token usage is reported separately in response.event events.
    """
    event_id: str
    type: Literal['session.usage.updated']
    usage: SessionUsage
    client_event_id: Optional[str] = None
    context_window: Optional[ContextWindow] = None
