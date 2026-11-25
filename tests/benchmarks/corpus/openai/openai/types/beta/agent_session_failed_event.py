# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .agent_session import AgentSession

class AgentSessionFailedEvent(BaseModel):
    """Emitted when a session fails."""
    event_id: str
    session: AgentSession
    type: Literal['agent.session.failed']
