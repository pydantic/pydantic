
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel
from .beta_browser_scroll_direction import BetaBrowserScrollDirection
from .beta_browser_coordinate_target import BetaBrowserCoordinateTarget

class BetaBrowserScrollInput(BaseModel):
    """Scroll at a viewport position. `target` must be a coordinate target."""
    scroll_direction: BetaBrowserScrollDirection
    target: BetaBrowserCoordinateTarget
    scroll_amount: Optional[int] = None
    tab_id: Optional[str] = None
