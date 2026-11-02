
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from pydantic import Field as FieldInfo
from ..._models import BaseModel
from .beta_browser_coordinate_target import BetaBrowserCoordinateTarget

class BetaBrowserLeftClickDragInput(BaseModel):
    """Press at `from`, drag to `target`, release. Both must be coordinate targets."""
    from_: BetaBrowserCoordinateTarget = FieldInfo(alias='from')
    target: BetaBrowserCoordinateTarget
    tab_id: Optional[str] = None
