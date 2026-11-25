
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsStaticBearerAuthResponse(BaseModel):
    """Static bearer token credential details for an MCP server."""
    mcp_server_url: str
    type: Literal['static_bearer']
