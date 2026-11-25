
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ...._models import BaseModel

class BetaPluginComponent(BaseModel):
    description: Optional[str] = None
    name: str
    type: Literal['agent', 'cli', 'command', 'hook', 'mcp_server', 'skill']
