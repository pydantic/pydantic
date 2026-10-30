
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel

class BetaBrowserWaitInput(BaseModel):
    """Pause for the given duration."""
    duration: float
    tab_id: Optional[str] = None
