
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsMCPEgressBlockedRunError(BaseModel):
    """
    An MCP server host used by the deployment's agent is blocked by the environment's network policy.
    """
    message: str
    type: Literal['mcp_egress_blocked_error']
