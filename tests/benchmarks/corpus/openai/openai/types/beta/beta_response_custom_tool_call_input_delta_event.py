# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Agent(BaseModel):
    """The agent that owns this multi-agent streaming event."""
    agent_name: str

class BetaResponseCustomToolCallInputDeltaEvent(BaseModel):
    """Event representing a delta (partial update) to the input of a custom tool call."""
    delta: str
    item_id: str
    output_index: int
    sequence_number: int
    type: Literal['response.custom_tool_call_input.delta']
    agent: Optional[Agent] = None
