
# Frozen model corpus; modified from anthropic 2.3.0; see README.md and LICENSE.
from typing_extensions import Literal
from .._models import BaseModel
from .tool_use_caller import ToolUseCaller
from .computer_scroll_input import ComputerScrollInput

class ComputerScrollToolUseBlock(BaseModel):
    id: str
    caller: ToolUseCaller
    input: ComputerScrollInput
    name: Literal['scroll']
    toolset_name: Literal['computer']
    type: Literal['tool_use']
