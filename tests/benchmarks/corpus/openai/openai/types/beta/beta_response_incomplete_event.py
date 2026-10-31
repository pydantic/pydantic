# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_response import BetaResponse

class Agent(BaseModel):
    """The agent that owns this multi-agent streaming event."""
    agent_name: str

class BetaResponseIncompleteEvent(BaseModel):
    """An event that is emitted when a response finishes as incomplete.

    Over WebSocket, steering can finish a response with
    `response.incomplete_details.reason` set to `steered`, followed automatically
    by a successor `response.created` that commits the queued steering input.
    """
    response: BetaResponse
    sequence_number: int
    type: Literal['response.incomplete']
    agent: Optional[Agent] = None
