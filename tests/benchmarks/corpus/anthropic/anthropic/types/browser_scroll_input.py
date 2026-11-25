
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from .._models import BaseModel
from .browser_scroll_direction import BrowserScrollDirection
from .browser_coordinate_target import BrowserCoordinateTarget

class BrowserScrollInput(BaseModel):
    """Scroll at a viewport position. `target` must be a coordinate target."""
    scroll_direction: BrowserScrollDirection
    target: BrowserCoordinateTarget
    scroll_amount: Optional[int] = None
    tab_id: Optional[str] = None
