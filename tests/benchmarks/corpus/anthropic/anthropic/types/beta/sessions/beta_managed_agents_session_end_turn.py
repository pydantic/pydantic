
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsSessionEndTurn(BaseModel):
    """The agent completed its turn naturally and is ready for the next user message."""
    type: Literal['end_turn']
