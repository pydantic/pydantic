
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from .._models import BaseModel
from .browser_ref_target import BrowserRefTarget
from .browser_form_input_value import BrowserFormInputValue

class BrowserFormInputInput(BaseModel):
    """Set the value of a form element (input, textarea, select, checkbox).

    Use a
    boolean for checkboxes, an option value or text for selects.
    """
    target: BrowserRefTarget
    value: BrowserFormInputValue
    tab_id: Optional[str] = None
