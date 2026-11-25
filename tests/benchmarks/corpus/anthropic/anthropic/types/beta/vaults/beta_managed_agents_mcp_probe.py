
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ...._models import BaseModel
from .beta_managed_agents_refresh_http_response import BetaManagedAgentsRefreshHTTPResponse

class BetaManagedAgentsMCPProbe(BaseModel):
    """The failing step of an MCP validation probe."""
    http_response: Optional[BetaManagedAgentsRefreshHTTPResponse] = None
    method: str
