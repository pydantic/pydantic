
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from ..._models import BaseModel

class BetaComputerLeftClickDragInput(BaseModel):
    """Click and drag the cursor from `start_coordinate` to `coordinate`."""
    coordinate: List[int]
    start_coordinate: List[int]
    text: Optional[str] = None
