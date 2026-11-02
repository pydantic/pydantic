
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel
from .beta_browser_click_target import BetaBrowserClickTarget

class BetaBrowserTripleClickInput(BaseModel):
    """
    Triple left-click at a viewport coordinate or on an element by reference
    (typically selects a line or paragraph).
    """
    target: BetaBrowserClickTarget
    modifiers: Optional[str] = None
    tab_id: Optional[str] = None
