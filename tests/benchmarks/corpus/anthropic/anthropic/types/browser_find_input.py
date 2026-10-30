
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from .._models import BaseModel

class BrowserFindInput(BaseModel):
    """Find elements matching a natural-language description (e.g.

    "search bar", "add to
    cart button") and return up to 20 matches with element references.
    """
    query: str
    tab_id: Optional[str] = None
