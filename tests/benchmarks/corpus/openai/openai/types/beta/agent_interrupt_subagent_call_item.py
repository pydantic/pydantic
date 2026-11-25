# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .agent_function_call_status import AgentFunctionCallStatus

class AgentInterruptSubagentCallItem(BaseModel):
    """A request to interrupt a subagent's current turn.

    The subagent remains available.
    """
    id: str
    recipient_agent_id: str
    sender_agent_id: str
    status: AgentFunctionCallStatus
    turn_id: str
    type: Literal['interrupt_subagent_call']
