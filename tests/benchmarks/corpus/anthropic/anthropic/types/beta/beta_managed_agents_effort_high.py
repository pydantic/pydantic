
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsEffortHigh(BaseModel):
    """High effort. Favors reasoning depth."""
    type: Literal['high']
