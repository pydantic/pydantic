
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel

class BetaManagedAgentsAgentToolset20260401EditInput(BaseModel):
    """Input payload for the `edit` tool.

    Performs a string
    replacement in the named file; by default `old_string` must
    occur exactly once.
    """
    file_path: str
    new_string: str
    old_string: str
    replace_all: Optional[bool] = None
