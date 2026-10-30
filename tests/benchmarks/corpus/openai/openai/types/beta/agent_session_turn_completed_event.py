# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .token_usage import TokenUsage
from .agents.sessions.turn import Turn

class AgentSessionTurnCompletedEvent(BaseModel):
    """Emitted when a turn completes."""
    event_id: str
    session_id: str
    turn: Turn
    turn_id: str
    type: Literal['agent.session.turn.completed']
    usage: Optional[TokenUsage] = None
