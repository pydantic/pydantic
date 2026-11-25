
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel

class BetaBrowserTypeInput(BaseModel):
    """Type a literal string at the current focus."""
    text: str
    tab_id: Optional[str] = None
