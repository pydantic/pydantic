
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_tool_use_caller import BetaToolUseCaller
from .beta_computer_left_mouse_up_input import BetaComputerLeftMouseUpInput

class BetaComputerLeftMouseUpToolUseBlock(BaseModel):
    id: str
    input: BetaComputerLeftMouseUpInput
    name: Literal['left_mouse_up']
    toolset_name: Literal['computer']
    type: Literal['tool_use']
    caller: Optional[BetaToolUseCaller] = None
