
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from .._models import BaseModel
from .browser_read_page_filter import BrowserReadPageFilter

class BrowserReadPageInput(BaseModel):
    """
    Return a structured accessibility tree of the page (or the subtree rooted at
    `ref`), with element references like [ref_7] that can be used as targets on later
    actions. Output is capped at 50,000 characters — narrow with `ref` or a smaller
    `depth` when exceeded.
    """
    depth: Optional[int] = None
    filter: Optional[BrowserReadPageFilter] = None
    ref: Optional[str] = None
    tab_id: Optional[str] = None
