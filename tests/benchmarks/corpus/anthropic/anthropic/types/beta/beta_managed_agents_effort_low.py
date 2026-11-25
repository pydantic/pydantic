
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsEffortLow(BaseModel):
    """Low effort. Favors latency over reasoning depth."""
    type: Literal['low']
