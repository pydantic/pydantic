# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List
from typing_extensions import Literal
from ..._models import BaseModel
from .agent_content import AgentContent
from .agent_function_call_status import AgentFunctionCallStatus

class AgentSendSubagentInputCallItem(BaseModel):
    """A request to send input to another agent."""
    id: str
    content: List[AgentContent]
    recipient_agent_id: str
    sender_agent_id: str
    status: AgentFunctionCallStatus
    turn_id: str
    type: Literal['send_subagent_input_call']
