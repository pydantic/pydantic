
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from .._models import BaseModel
from .browser_ref_target import BrowserRefTarget

class BrowserFileUploadInput(BaseModel):
    """Set the value of a file-input element to one or more files.

    The target must be an
    element reference; at least one of paths or document_ids is required.
    """
    target: BrowserRefTarget
    document_ids: Optional[List[str]] = None
    paths: Optional[List[str]] = None
    tab_id: Optional[str] = None
