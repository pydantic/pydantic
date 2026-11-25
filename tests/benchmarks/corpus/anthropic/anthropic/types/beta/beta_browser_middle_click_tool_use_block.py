
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_tool_use_caller import BetaToolUseCaller
from .beta_browser_middle_click_input import BetaBrowserMiddleClickInput

class BetaBrowserMiddleClickToolUseBlock(BaseModel):
    id: str
    input: BetaBrowserMiddleClickInput
    name: Literal['middle_click']
    toolset_name: Literal['browser']
    type: Literal['tool_use']
    caller: Optional[BetaToolUseCaller] = None
