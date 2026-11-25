
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from .._models import BaseModel
from .browser_coordinate_target import BrowserCoordinateTarget

class BrowserLeftMouseDownInput(BaseModel):
    """Press and hold the left mouse button at a viewport coordinate.

    Pair with
    left_mouse_up to perform a custom drag.
    """
    target: BrowserCoordinateTarget
    tab_id: Optional[str] = None
