
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsWebFetchURLSourceToolReference(BaseModel):
    """Names one tool in an only or except list."""
    name: str
    type: Literal['tool_reference']
