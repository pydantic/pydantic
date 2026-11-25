
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from .._models import BaseModel
from .browser_click_target import BrowserClickTarget

class BrowserHoverInput(BaseModel):
    """Move the cursor to a coordinate or element without clicking."""
    target: BrowserClickTarget
    tab_id: Optional[str] = None
