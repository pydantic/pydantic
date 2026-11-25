# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import List, Optional
from typing_extensions import Literal
from ..._models import BaseModel

class Tool(BaseModel):
    """A tool available on an MCP server."""
    input_schema: object
    name: str
    annotations: Optional[object] = None
    description: Optional[str] = None

class RealtimeMcpListTools(BaseModel):
    """A Realtime item listing tools available on an MCP server."""
    server_label: str
    tools: List[Tool]
    type: Literal['mcp_list_tools']
    id: Optional[str] = None
