
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsEffortMax(BaseModel):
    """Maximum effort. Favors reasoning depth over latency."""
    type: Literal['max']
