# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Agent(BaseModel):
    """The agent that owns this multi-agent streaming event."""
    agent_name: str

class BetaResponseReasoningTextDoneEvent(BaseModel):
    """Emitted when a reasoning text is completed."""
    content_index: int
    item_id: str
    output_index: int
    sequence_number: int
    text: str
    type: Literal['response.reasoning_text.done']
    agent: Optional[Agent] = None
