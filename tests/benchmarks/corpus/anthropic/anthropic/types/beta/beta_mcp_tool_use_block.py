
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Dict
from typing_extensions import Literal
from ..._models import BaseModel

class BetaMCPToolUseBlock(BaseModel):
    id: str
    input: Dict[str, object]
    name: str
    server_name: str
    type: Literal['mcp_tool_use']
