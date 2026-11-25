# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_response import BetaResponse

class Agent(BaseModel):
    """The agent that owns this multi-agent streaming event."""
    agent_name: str

class BetaResponseQueuedEvent(BaseModel):
    """Emitted when a response is queued and waiting to be processed."""
    response: BetaResponse
    sequence_number: int
    type: Literal['response.queued']
    agent: Optional[Agent] = None
