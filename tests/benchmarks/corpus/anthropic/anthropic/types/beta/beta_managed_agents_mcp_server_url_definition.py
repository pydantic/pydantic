
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsMCPServerURLDefinition(BaseModel):
    """URL-based MCP server connection as returned in API responses."""
    name: str
    type: Literal['url']
    url: str
