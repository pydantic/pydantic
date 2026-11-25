
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel

class BetaBrowserSwitchTabConfig(BaseModel):
    """``switch_tab``'s config overrides."""
    defer_loading: Optional[bool] = None
    enabled: Optional[bool] = None
