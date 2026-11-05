# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Agent(BaseModel):
    """The agent that owns this multi-agent streaming event."""
    agent_name: str

class BetaResponseAudioDeltaEvent(BaseModel):
    """Emitted when there is a partial audio response."""
    delta: str
    sequence_number: int
    type: Literal['response.audio.delta']
    agent: Optional[Agent] = None
