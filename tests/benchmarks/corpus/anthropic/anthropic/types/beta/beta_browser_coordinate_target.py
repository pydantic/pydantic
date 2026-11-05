
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from ..._models import BaseModel

class BetaBrowserCoordinateTarget(BaseModel):
    """
    A point in the browser viewport, in viewport pixels (the same frame as a
    full-viewport screenshot).
    """
    type: Literal['coordinate']
    x: int
    y: int
