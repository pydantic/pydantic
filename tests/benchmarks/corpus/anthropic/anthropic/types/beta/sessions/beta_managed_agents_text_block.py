
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ...._models import BaseModel

class BetaManagedAgentsTextBlock(BaseModel):
    """Regular text content."""
    text: str
    type: Literal['text']
