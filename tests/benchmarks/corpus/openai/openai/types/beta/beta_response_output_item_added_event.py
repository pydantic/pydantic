# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_response_output_item import BetaResponseOutputItem

class Agent(BaseModel):
    """The agent that owns this multi-agent streaming event."""
    agent_name: str

class BetaResponseOutputItemAddedEvent(BaseModel):
    """Emitted when a new output item is added."""
    item: BetaResponseOutputItem
    output_index: int
    sequence_number: int
    type: Literal['response.output_item.added']
    agent: Optional[Agent] = None
