
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_mcp_tool import BetaMCPTool

class BetaMCPToolListingBlock(BaseModel):
    """
    The tool listing the server fetched from an MCP server while producing
    this response. Send the assistant message back unchanged, this block
    included, so later requests use this listing instead of asking the MCP
    server again.
    """
    mcp_server_name: str
    tools: List[BetaMCPTool]
    type: Literal['mcp_tool_listing']
