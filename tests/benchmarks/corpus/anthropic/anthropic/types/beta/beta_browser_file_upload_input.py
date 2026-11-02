
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from ..._models import BaseModel
from .beta_browser_ref_target import BetaBrowserRefTarget

class BetaBrowserFileUploadInput(BaseModel):
    """Set the value of a file-input element to one or more files.

    The target must be an
    element reference; at least one of paths or document_ids is required.
    """
    target: BetaBrowserRefTarget
    document_ids: Optional[List[str]] = None
    paths: Optional[List[str]] = None
    tab_id: Optional[str] = None
