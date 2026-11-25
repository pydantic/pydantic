
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel

class BetaManagedAgentsAgentToolset20260401GrepInput(BaseModel):
    """Input payload for the `grep` tool.

    Searches file contents for
    a regular expression, returning matching lines.
    """
    pattern: str
    path: Optional[str] = None
