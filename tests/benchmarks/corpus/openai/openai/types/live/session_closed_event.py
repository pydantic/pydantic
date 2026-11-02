# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .session_usage import SessionUsage
from .session_resource import SessionResource

class SessionClosedEvent(BaseModel):
    """
    Returned after the Live session finishes finalizing, with the close reason, final session snapshot, and cumulative audio usage. A connection closing without this event does not confirm successful finalization.
    """
    event_id: str
    reason: Literal['close_requested', 'expired', 'content', 'remote_hangup', 'connection_lost']
    session: SessionResource
    type: Literal['session.closed']
    usage: SessionUsage
    client_event_id: Optional[str] = None
