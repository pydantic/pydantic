
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from .._models import BaseModel

class BrowserSwitchTabInput(BaseModel):
    """
    Make the tab with the given tab_id the active tab — the tab that actions without
    a tab_id apply to.
    """
    tab_id: str
