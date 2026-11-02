# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .output_text import OutputText
from .agent_output_item_status import AgentOutputItemStatus

class AgentSessionAssistantMessage(BaseModel):
    """An assistant message produced by the agent."""
    id: str
    content: List[OutputText]
    phase: Optional[Literal['commentary', 'final_answer']] = None
    role: Literal['assistant']
    status: AgentOutputItemStatus
    turn_id: str
    type: Literal['message']
