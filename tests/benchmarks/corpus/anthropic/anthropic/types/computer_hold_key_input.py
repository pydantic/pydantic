
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from .._models import BaseModel

class ComputerHoldKeyInput(BaseModel):
    """Hold down a key or key-combination for a specified duration.

    Uses the same key
    syntax as `key`.
    """
    duration: int
    text: str
