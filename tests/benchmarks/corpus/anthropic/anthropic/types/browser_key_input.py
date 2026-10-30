
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from .._models import BaseModel

class BrowserKeyInput(BaseModel):
    """Press a key or key chord.

    Use "+" to combine modifiers with a key (e.g. "ctrl+a",
    "cmd+shift+p") and space to sequence presses (e.g. "Backspace Backspace Delete").
    Common names like "Return", "Tab", "Escape", "BackSpace" are supported.
    """
    text: str
    repeat: Optional[int] = None
    tab_id: Optional[str] = None
