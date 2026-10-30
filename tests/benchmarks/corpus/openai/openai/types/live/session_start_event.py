# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .session_config import SessionConfig

class SessionStartEvent(BaseModel):
    """Start a Live session on a primary WebSocket.

    Send this event before other commands and wait for `session.started`.
    """
    session: SessionConfig
    type: Literal['session.start']
    event_id: Optional[str] = None
