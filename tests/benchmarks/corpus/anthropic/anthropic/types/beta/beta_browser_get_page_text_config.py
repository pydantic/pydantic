
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel

class BetaBrowserGetPageTextConfig(BaseModel):
    """``get_page_text``'s config overrides."""
    defer_loading: Optional[bool] = None
    enabled: Optional[bool] = None
