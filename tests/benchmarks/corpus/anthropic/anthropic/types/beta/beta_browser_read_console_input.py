
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel

class BetaBrowserReadConsoleInput(BaseModel):
    """
    Return console output (log entries, errors, warnings) accumulated since the
    driver attached to the tab and since the last read, one line per entry. An empty
    result does not mean no traffic for a tab that predates attach.
    """
    tab_id: Optional[str] = None
