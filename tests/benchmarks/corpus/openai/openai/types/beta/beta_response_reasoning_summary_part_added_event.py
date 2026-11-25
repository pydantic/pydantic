# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Part(BaseModel):
    """The summary part that was added."""
    text: str
    type: Literal['summary_text']

class Agent(BaseModel):
    """The agent that owns this multi-agent streaming event."""
    agent_name: str

class BetaResponseReasoningSummaryPartAddedEvent(BaseModel):
    """Emitted when a new reasoning summary part is added."""
    item_id: str
    output_index: int
    part: Part
    sequence_number: int
    summary_index: int
    type: Literal['response.reasoning_summary_part.added']
    agent: Optional[Agent] = None
