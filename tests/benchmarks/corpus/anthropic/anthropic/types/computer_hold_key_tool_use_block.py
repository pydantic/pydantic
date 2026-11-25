
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .tool_use_caller import ToolUseCaller
from .computer_hold_key_input import ComputerHoldKeyInput

class ComputerHoldKeyToolUseBlock(BaseModel):
    id: str
    caller: ToolUseCaller
    input: ComputerHoldKeyInput
    name: Literal['hold_key']
    toolset_name: Literal['computer']
    type: Literal['tool_use']
