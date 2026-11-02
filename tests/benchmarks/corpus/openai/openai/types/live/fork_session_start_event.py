# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .fork_session_config import ForkSessionConfig

class ForkSessionStartEvent(BaseModel):
    """Start a Live session after connecting to a stored session’s fork WebSocket.

    Send an empty `session` object to use the stored configuration.
    """
    session: ForkSessionConfig
    type: Literal['session.start']
    event_id: Optional[str] = None
