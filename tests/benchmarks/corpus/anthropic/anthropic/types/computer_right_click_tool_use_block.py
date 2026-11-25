
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .tool_use_caller import ToolUseCaller
from .computer_right_click_input import ComputerRightClickInput

class ComputerRightClickToolUseBlock(BaseModel):
    id: str
    caller: ToolUseCaller
    input: ComputerRightClickInput
    name: Literal['right_click']
    toolset_name: Literal['computer']
    type: Literal['tool_use']
