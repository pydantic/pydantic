
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsMCPEgressBlockedDeploymentPausedReasonError(BaseModel):
    """
    An MCP server host used by the deployment's agent is blocked by the environment's network policy.
    """
    type: Literal['mcp_egress_blocked_error']
