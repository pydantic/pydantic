
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_tool_use_caller import BetaToolUseCaller
from .beta_computer_right_click_input import BetaComputerRightClickInput

class BetaComputerRightClickToolUseBlock(BaseModel):
    id: str
    input: BetaComputerRightClickInput
    name: Literal['right_click']
    toolset_name: Literal['computer']
    type: Literal['tool_use']
    caller: Optional[BetaToolUseCaller] = None
