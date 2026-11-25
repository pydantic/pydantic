# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ....._models import BaseModel
from ...token_usage import TokenUsage
from ...session_turn_error import SessionTurnError

class Turn(BaseModel):
    """The canonical public representation of a session turn."""
    id: str
    agent_id: str
    completed_at: Optional[int] = None
    created_at: int
    error: Optional[SessionTurnError] = None
    object: Literal['agent.session.turn']
    session_id: str
    started_at: Optional[int] = None
    status: Literal['queued', 'in_progress', 'waiting', 'completed', 'failed', 'cancelled']
    subagent_id: Optional[str] = None
    usage: Optional[TokenUsage] = None
