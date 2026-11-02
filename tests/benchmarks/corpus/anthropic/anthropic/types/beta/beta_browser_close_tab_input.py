
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from ..._models import BaseModel

class BetaBrowserCloseTabInput(BaseModel):
    """Close the tab with the given tab_id."""
    tab_id: str
