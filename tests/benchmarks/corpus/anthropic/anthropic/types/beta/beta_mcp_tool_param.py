
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict, Optional
from ..._models import BaseModel

class BetaMCPToolParam(BaseModel):
    """
    A tool as an MCP server lists it: its name on that server, its
    description, and its input schema.
    """
    input_schema: Dict[str, object]
    name: str
    description: Optional[str] = None
