# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel

class LogprobTopLogprob(BaseModel):
    token: Optional[str] = None
    logprob: Optional[float] = None

class Logprob(BaseModel):
    """
    A logprob is the logarithmic probability that the model assigns to producing
    a particular token at a given position in the sequence. Less-negative (higher)
    logprob values indicate greater model confidence in that token choice.
    """
    token: str
    logprob: float
    top_logprobs: Optional[List[LogprobTopLogprob]] = None

class Agent(BaseModel):
    """The agent that owns this multi-agent streaming event."""
    agent_name: str

class BetaResponseTextDoneEvent(BaseModel):
    """Emitted when text content is finalized."""
    content_index: int
    item_id: str
    logprobs: List[Logprob]
    output_index: int
    sequence_number: int
    text: str
    type: Literal['response.output_text.done']
    agent: Optional[Agent] = None
