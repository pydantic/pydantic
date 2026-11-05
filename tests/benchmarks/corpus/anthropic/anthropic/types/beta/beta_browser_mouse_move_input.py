
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel
from .beta_browser_coordinate_target import BetaBrowserCoordinateTarget

class BetaBrowserMouseMoveInput(BaseModel):
    """Move the pointer to a viewport coordinate without clicking."""
    target: BetaBrowserCoordinateTarget
    tab_id: Optional[str] = None
