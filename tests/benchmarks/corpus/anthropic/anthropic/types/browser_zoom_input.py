
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import List, Optional
from .._models import BaseModel

class BrowserZoomInput(BaseModel):
    """
    Return a cropped screenshot of the given viewport region, scaled up for closer
    inspection — useful for small icons, buttons, or text. Coordinates are in the
    same viewport-pixel space as a full screenshot.
    """
    region: List[int]
    tab_id: Optional[str] = None
