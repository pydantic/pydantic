
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from pydantic import Field as FieldInfo
from .._models import BaseModel
from .browser_coordinate_target import BrowserCoordinateTarget

class BrowserLeftClickDragInput(BaseModel):
    """Press at `from`, drag to `target`, release. Both must be coordinate targets."""
    from_: BrowserCoordinateTarget = FieldInfo(alias='from')
    target: BrowserCoordinateTarget
    tab_id: Optional[str] = None
