
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_tool_use_caller import BetaToolUseCaller
from .beta_computer_mouse_move_input import BetaComputerMouseMoveInput

class BetaComputerMouseMoveToolUseBlock(BaseModel):
    id: str
    input: BetaComputerMouseMoveInput
    name: Literal['mouse_move']
    toolset_name: Literal['computer']
    type: Literal['tool_use']
    caller: Optional[BetaToolUseCaller] = None
