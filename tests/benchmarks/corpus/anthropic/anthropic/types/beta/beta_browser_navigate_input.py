
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel

class BetaBrowserNavigateInput(BaseModel):
    """Navigate to a URL, or go back/forward/reload in history.

    The protocol may be
    omitted (defaults to https://).
    """
    url: str
    tab_id: Optional[str] = None
