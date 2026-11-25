
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List
from .._models import BaseModel

class ComputerMouseMoveInput(BaseModel):
    """Move the cursor to a specified (x, y) pixel coordinate.

    Use this ONLY to hover
    without clicking; otherwise use a click action directly.
    """
    coordinate: List[int]
