
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .tool_use_caller import ToolUseCaller
from .computer_left_mouse_down_input import ComputerLeftMouseDownInput

class ComputerLeftMouseDownToolUseBlock(BaseModel):
    id: str
    caller: ToolUseCaller
    input: ComputerLeftMouseDownInput
    name: Literal['left_mouse_down']
    toolset_name: Literal['computer']
    type: Literal['tool_use']
