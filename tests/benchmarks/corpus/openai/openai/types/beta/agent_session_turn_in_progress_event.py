# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .agents.sessions.turn import Turn

class AgentSessionTurnInProgressEvent(BaseModel):
    """Emitted when a turn starts running."""
    event_id: str
    session_id: str
    turn: Turn
    turn_id: str
    type: Literal['agent.session.turn.in_progress']
