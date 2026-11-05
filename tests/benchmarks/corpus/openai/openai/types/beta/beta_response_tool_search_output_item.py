# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_tool import BetaTool

class Agent(BaseModel):
    """The agent that produced this item."""
    agent_name: str

class BetaResponseToolSearchOutputItem(BaseModel):
    id: str
    call_id: Optional[str] = None
    execution: Literal['server', 'client']
    status: Literal['in_progress', 'completed', 'incomplete']
    tools: List[BetaTool]
    type: Literal['tool_search_output']
    agent: Optional[Agent] = None
    created_by: Optional[str] = None
