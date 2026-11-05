
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .tool_use_caller import ToolUseCaller
from .computer_left_mouse_up_input import ComputerLeftMouseUpInput

class ComputerLeftMouseUpToolUseBlock(BaseModel):
    id: str
    caller: ToolUseCaller
    input: ComputerLeftMouseUpInput
    name: Literal['left_mouse_up']
    toolset_name: Literal['computer']
    type: Literal['tool_use']
