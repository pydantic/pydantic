# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .agent_output_item_status import AgentOutputItemStatus
from .agent_session_message_content import AgentSessionMessageContent

class AgentSessionMessage(BaseModel):
    """A user or assistant message recorded in a session."""
    id: Optional[str] = None
    content: List[AgentSessionMessageContent]
    phase: Optional[Literal['commentary', 'final_answer']] = None
    role: Literal['user', 'assistant']
    status: AgentOutputItemStatus
    turn_id: str
    type: Literal['message']
