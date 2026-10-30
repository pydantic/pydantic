
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .tool_use_caller import ToolUseCaller
from .computer_left_click_drag_input import ComputerLeftClickDragInput

class ComputerLeftClickDragToolUseBlock(BaseModel):
    id: str
    caller: ToolUseCaller
    input: ComputerLeftClickDragInput
    name: Literal['left_click_drag']
    toolset_name: Literal['computer']
    type: Literal['tool_use']
