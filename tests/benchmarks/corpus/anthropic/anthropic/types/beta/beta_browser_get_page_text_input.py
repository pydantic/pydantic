
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel

class BetaBrowserGetPageTextInput(BaseModel):
    """
    Return the page's visible text content as plain text, prioritizing article
    content. Suited to articles, documentation, and other text-heavy pages.
    """
    tab_id: Optional[str] = None
