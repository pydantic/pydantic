
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsAgentReference(BaseModel):
    """A resolved agent reference with a concrete version."""
    id: str
    type: Literal['agent']
    version: int
