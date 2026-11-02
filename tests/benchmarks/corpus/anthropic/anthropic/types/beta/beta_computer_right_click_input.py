
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from ..._models import BaseModel

class BetaComputerRightClickInput(BaseModel):
    """
    Click the right mouse button at the specified (x, y) pixel coordinate, or the
    current cursor position if `coordinate` is omitted.
    """
    coordinate: Optional[List[int]] = None
    text: Optional[str] = None
