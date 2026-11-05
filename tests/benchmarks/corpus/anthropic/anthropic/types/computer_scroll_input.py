
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from .._models import BaseModel
from .computer_scroll_direction import ComputerScrollDirection

class ComputerScrollInput(BaseModel):
    """
    Scroll the screen at the specified (x, y) pixel coordinate, or the current cursor
    position if `coordinate` is omitted. Do NOT use PageUp/PageDown to scroll.
    """
    scroll_amount: int
    scroll_direction: ComputerScrollDirection
    coordinate: Optional[List[int]] = None
    text: Optional[str] = None
