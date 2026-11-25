
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ..._models import BaseModel

class BetaManagedAgentsAgentToolset20260401WriteInput(BaseModel):
    """Input payload for the `write` tool.

    Writes (overwriting) the
    entire file contents.
    """
    content: str
    file_path: str
