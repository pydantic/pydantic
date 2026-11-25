
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from datetime import datetime
from typing_extensions import Literal
from ...._models import BaseModel
from .beta_managed_agents_mcp_oauth_refresh_response import BetaManagedAgentsMCPOAuthRefreshResponse

class BetaManagedAgentsMCPOAuthAuthResponse(BaseModel):
    """OAuth credential details for an MCP server."""
    mcp_server_url: str
    type: Literal['mcp_oauth']
    expires_at: Optional[datetime] = None
    refresh: Optional[BetaManagedAgentsMCPOAuthRefreshResponse] = None
