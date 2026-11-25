
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel

class BetaManagedAgentsAgentToolset20260401GlobInput(BaseModel):
    """Input payload for the `glob` tool.

    Returns paths matching a
    doublestar glob pattern, newest first.
    """
    pattern: str
    path: Optional[str] = None
