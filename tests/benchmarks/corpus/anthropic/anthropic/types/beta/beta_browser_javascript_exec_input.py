
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel

class BetaBrowserJavascriptExecInput(BaseModel):
    """
    Execute JavaScript in the page context and return the value of the last
    expression. The code runs with access to the DOM, `window`, and page variables.
    Write the expression you want evaluated — do NOT use `return`.
    """
    text: str
    tab_id: Optional[str] = None
