
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from ..._models import BaseModel

class BetaManagedAgentsAgentToolset20260401ReadInput(BaseModel):
    """Input payload for the `read` tool.

    Reads file contents
    relative to the runner's working directory (or absolute when
    the runner permits).
    """
    file_path: str
    view_range: Optional[List[int]] = None
