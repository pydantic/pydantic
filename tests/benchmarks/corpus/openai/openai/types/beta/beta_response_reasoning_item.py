# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Summary(BaseModel):
    """A summary text from the model."""
    text: str
    type: Literal['summary_text']

class Agent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class Content(BaseModel):
    """Reasoning text from the model."""
    text: str
    type: Literal['reasoning_text']

class BetaResponseReasoningItem(BaseModel):
    """
    A description of the chain of thought used by a reasoning model while generating
    a response. Be sure to include these items in your `input` to the Responses API
    for subsequent turns of a conversation if you are manually
    [managing context](https://developers.openai.com/api/docs/guides/conversation-state).
    """
    id: str
    summary: List[Summary]
    type: Literal['reasoning']
    agent: Optional[Agent] = None
    content: Optional[List[Content]] = None
    encrypted_content: Optional[str] = None
    status: Optional[Literal['in_progress', 'completed', 'incomplete']] = None
