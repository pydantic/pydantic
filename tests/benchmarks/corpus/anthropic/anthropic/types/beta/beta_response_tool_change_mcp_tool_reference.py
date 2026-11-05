
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaResponseToolChangeMCPToolReference(BaseModel):
    """
    Reference to a single MCP tool, by its server and its name on that
    server, as a ``compaction`` block's ``tool_changes`` entry reports it.
    Send it back unchanged with the block.
    """
    name: str
    server_name: str
    type: Literal['mcp_tool_reference']
