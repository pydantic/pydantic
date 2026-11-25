# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Part(BaseModel):
    """The completed summary part."""
    text: str
    type: Literal['summary_text']

class Agent(BaseModel):
    """The agent that owns this multi-agent streaming event."""
    agent_name: str

class BetaResponseReasoningSummaryPartDoneEvent(BaseModel):
    """Emitted when a reasoning summary part is completed."""
    item_id: str
    output_index: int
    part: Part
    sequence_number: int
    summary_index: int
    type: Literal['response.reasoning_summary_part.done']
    agent: Optional[Agent] = None
    status: Optional[Literal['incomplete']] = None
