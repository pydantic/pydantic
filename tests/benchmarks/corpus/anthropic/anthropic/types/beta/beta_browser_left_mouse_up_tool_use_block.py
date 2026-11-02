
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_tool_use_caller import BetaToolUseCaller
from .beta_browser_left_mouse_up_input import BetaBrowserLeftMouseUpInput

class BetaBrowserLeftMouseUpToolUseBlock(BaseModel):
    id: str
    input: BetaBrowserLeftMouseUpInput
    name: Literal['left_mouse_up']
    toolset_name: Literal['browser']
    type: Literal['tool_use']
    caller: Optional[BetaToolUseCaller] = None
