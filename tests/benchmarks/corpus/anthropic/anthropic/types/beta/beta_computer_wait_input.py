
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ..._models import BaseModel

class BetaComputerWaitInput(BaseModel):
    """Wait for a specified duration."""
    duration: int
