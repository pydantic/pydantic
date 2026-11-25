# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel
from .agent_function_call_status import AgentFunctionCallStatus

class AgentMcpCallItem(BaseModel):
    """A call to a tool on an MCP server."""
    id: str
    arguments: object
    error: object
    name: str
    output: object
    server_label: str
    status: AgentFunctionCallStatus
    turn_id: str
    type: Literal['mcp_call']
