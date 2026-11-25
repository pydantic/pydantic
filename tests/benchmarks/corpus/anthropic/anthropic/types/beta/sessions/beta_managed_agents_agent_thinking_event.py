
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsAgentThinkingEvent(BaseModel):
    """Indicates the agent is making forward progress via extended thinking.

    A progress signal, not a content carrier.
    """
    id: str
    processed_at: datetime
    type: Literal['agent.thinking']
