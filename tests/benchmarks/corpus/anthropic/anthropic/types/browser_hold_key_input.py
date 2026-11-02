
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from .._models import BaseModel

class BrowserHoldKeyInput(BaseModel):
    """Hold a key or key chord down for a duration, then release it.

    Uses the same key
    names and "+" chord syntax as the key action.
    """
    duration: float
    text: str
    tab_id: Optional[str] = None
