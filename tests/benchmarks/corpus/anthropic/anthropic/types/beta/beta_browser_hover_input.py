
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel
from .beta_browser_click_target import BetaBrowserClickTarget

class BetaBrowserHoverInput(BaseModel):
    """Move the cursor to a coordinate or element without clicking."""
    target: BetaBrowserClickTarget
    tab_id: Optional[str] = None
