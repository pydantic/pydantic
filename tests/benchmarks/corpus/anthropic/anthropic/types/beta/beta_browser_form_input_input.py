
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from ..._models import BaseModel
from .beta_browser_ref_target import BetaBrowserRefTarget
from .beta_browser_form_input_value import BetaBrowserFormInputValue

class BetaBrowserFormInputInput(BaseModel):
    """Set the value of a form element (input, textarea, select, checkbox).

    Use a
    boolean for checkboxes, an option value or text for selects.
    """
    target: BetaBrowserRefTarget
    value: BetaBrowserFormInputValue
    tab_id: Optional[str] = None
