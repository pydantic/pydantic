
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing import Optional
from typing_extensions import Literal
from ..._models import BaseModel
from .beta_tool_use_caller import BetaToolUseCaller
from .beta_computer_hold_key_input import BetaComputerHoldKeyInput

class BetaComputerHoldKeyToolUseBlock(BaseModel):
    id: str
    input: BetaComputerHoldKeyInput
    name: Literal['hold_key']
    toolset_name: Literal['computer']
    type: Literal['tool_use']
    caller: Optional[BetaToolUseCaller] = None
