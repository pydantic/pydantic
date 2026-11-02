
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .tool_use_caller import ToolUseCaller
from .computer_middle_click_input import ComputerMiddleClickInput

class ComputerMiddleClickToolUseBlock(BaseModel):
    id: str
    caller: ToolUseCaller
    input: ComputerMiddleClickInput
    name: Literal['middle_click']
    toolset_name: Literal['computer']
    type: Literal['tool_use']
