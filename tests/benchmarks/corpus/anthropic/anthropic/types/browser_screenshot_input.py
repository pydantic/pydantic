
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from .._models import BaseModel

class BrowserScreenshotInput(BaseModel):
    """Capture the current browser viewport."""
    tab_id: Optional[str] = None
