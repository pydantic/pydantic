
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from .._models import BaseModel
from .browser_ref_target import BrowserRefTarget

class BrowserScrollToInput(BaseModel):
    """Scroll an element into view."""
    target: BrowserRefTarget
    tab_id: Optional[str] = None
