# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .agent_session_environment_state import AgentSessionEnvironmentState

class AgentSessionEnvironmentConnectedEvent(BaseModel):
    """Emitted when a session environment connects."""
    environment: AgentSessionEnvironmentState
    event_id: str
    session_id: str
    turn_id: Optional[str] = None
    type: Literal['agent.session.environment.connected']
