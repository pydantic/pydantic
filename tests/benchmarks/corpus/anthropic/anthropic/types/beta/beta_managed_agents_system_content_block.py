
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaManagedAgentsSystemContentBlock(BaseModel):
    """Content block in a mid-conversation system message. Text-only."""
    text: str
    type: Literal['text']
