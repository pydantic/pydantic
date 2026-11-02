# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .summary_text import SummaryText
from .agent_output_item_status import AgentOutputItemStatus

class AgentReasoningItem(BaseModel):
    """A reasoning item produced by the agent."""
    id: str
    status: Optional[AgentOutputItemStatus] = None
    summary: List[SummaryText]
    turn_id: str
    type: Literal['reasoning']
