
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List
from ..._models import BaseModel

class BetaComputerZoomInput(BaseModel):
    """Take a screenshot of a rectangular region.

    Region coordinates are in the
    full-screenshot space (not physical display pixels). The crop is scaled up to
    fill the image budget so fine details become legible.
    """
    region: List[int]
