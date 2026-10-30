# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Agent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class BetaResponseToolSearchCall(BaseModel):
    id: str
    arguments: object
    call_id: Optional[str] = None
    execution: Literal['server', 'client']
    status: Literal['in_progress', 'completed', 'incomplete']
    type: Literal['tool_search_call']
    agent: Optional[Agent] = None
    created_by: Optional[str] = None
