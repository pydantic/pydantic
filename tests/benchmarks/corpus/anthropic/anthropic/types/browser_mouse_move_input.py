
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from .._models import BaseModel
from .browser_coordinate_target import BrowserCoordinateTarget

class BrowserMouseMoveInput(BaseModel):
    """Move the pointer to a viewport coordinate without clicking."""
    target: BrowserCoordinateTarget
    tab_id: Optional[str] = None
