# File generated from our OpenAPI spec by Castiron. See CONTRIBUTING.md for details.

# Frozen model corpus; modified from openai 3.41.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel

class ToolChoiceMcp(BaseModel):
    """
    Use this option to force the model to call a specific tool on a remote MCP server.
    """
    server_label: str
    type: Literal['mcp']
    name: Optional[str] = None
