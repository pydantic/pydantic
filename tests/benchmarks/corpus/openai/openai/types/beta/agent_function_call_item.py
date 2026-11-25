# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .agent_function_call_status import AgentFunctionCallStatus

class AgentFunctionCallItem(BaseModel):
    """A function call produced by the agent."""
    id: str
    arguments: object
    call_id: str
    name: str
    status: AgentFunctionCallStatus
    turn_id: str
    type: Literal['function_call']
