# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class AgentSessionEnvironmentResetEvent(BaseModel):
    """Emitted after a hosted sandbox is replaced.

    Conversation history survives; changes to the previous sandbox's files and processes do not.
    """
    environment_id: str
    event_id: str
    reset_count: int
    session_id: str
    turn_id: Optional[str] = None
    type: Literal['agent.session.environment.reset']
