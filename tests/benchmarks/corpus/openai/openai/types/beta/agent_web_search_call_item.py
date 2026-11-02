# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .web_search_action import WebSearchAction
from .agent_output_item_status import AgentOutputItemStatus

class AgentWebSearchCallItem(BaseModel):
    """A web search call produced by the agent."""
    id: str
    action: Optional[WebSearchAction] = None
    status: AgentOutputItemStatus
    turn_id: str
    type: Literal['web_search_call']
