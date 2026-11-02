
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel
from .beta_browser_ref_target import BetaBrowserRefTarget

class BetaBrowserScrollToInput(BaseModel):
    """Scroll an element into view."""
    target: BetaBrowserRefTarget
    tab_id: Optional[str] = None
