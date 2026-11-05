# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .session_error import SessionError

class AgentSessionErrorEvent(BaseModel):
    """Emitted when a turn or session fails."""
    error: SessionError
    event_id: str
    session_id: str
    type: Literal['error']
