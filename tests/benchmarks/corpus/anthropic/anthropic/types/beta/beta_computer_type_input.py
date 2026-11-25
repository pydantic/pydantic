
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ..._models import BaseModel

class BetaComputerTypeInput(BaseModel):
    """Type a string of text on the keyboard."""
    text: str
