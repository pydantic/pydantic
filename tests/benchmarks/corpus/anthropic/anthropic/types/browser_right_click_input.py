
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from .._models import BaseModel
from .browser_click_target import BrowserClickTarget

class BrowserRightClickInput(BaseModel):
    """Right-click at a viewport coordinate or on an element by reference."""
    target: BrowserClickTarget
    modifiers: Optional[str] = None
    tab_id: Optional[str] = None
