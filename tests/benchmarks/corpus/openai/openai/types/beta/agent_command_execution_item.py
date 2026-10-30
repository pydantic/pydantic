# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .agent_function_call_status import AgentFunctionCallStatus

class AgentCommandExecutionItem(BaseModel):
    """A command execution produced by the agent."""
    id: str
    command: str
    cwd: Optional[str] = None
    duration_ms: Optional[int] = None
    exit_code: Optional[int] = None
    output: Optional[str] = None
    status: AgentFunctionCallStatus
    turn_id: str
    type: Literal['command_execution']
