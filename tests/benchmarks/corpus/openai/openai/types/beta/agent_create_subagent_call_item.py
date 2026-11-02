# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .agent_content import AgentContent
from .agent_function_call_status import AgentFunctionCallStatus

class AgentCreateSubagentCallItem(BaseModel):
    """A request to spawn a subagent."""
    id: str
    agent_id: str
    content: List[AgentContent]
    model: Optional[str] = None
    reasoning_effort: Optional[str] = None
    status: AgentFunctionCallStatus
    turn_id: str
    type: Literal['create_subagent_call']
